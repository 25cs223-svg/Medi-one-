from flask_wtf.csrf import generate_csrf
import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse
from app.extensions import limiter


import psycopg
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    current_app,
    url_for
)
from werkzeug.security import generate_password_hash, check_password_hash

from app.services.email_service import send_verification_email


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing")

    return psycopg.connect(database_url, connect_timeout=10)


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_valid_email(email):
    import re

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))


def generate_verification_token():
    return secrets.token_urlsafe(32)


def create_verification_url(token):
    base_url = os.getenv("APP_BASE_URL")

    if not base_url:
        raise RuntimeError("APP_BASE_URL is not configured")

    return urljoin(
        base_url.rstrip("/") + "/",
        url_for("auth.verify_email", token=token).lstrip("/")
    )
@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip().lower()
    license_number = (data.get("license_number") or "").strip()
    specialization = (data.get("specialization") or "").strip()

    if not full_name or not is_valid_email(email):
        return jsonify({"error": "Valid name and email are required"}), 400

    if len(password) < 12:
        return jsonify({"error": "Password must contain at least 12 characters"}), 400

    if role not in ("patient", "doctor"):
        return jsonify({"error": "Invalid account role"}), 400

    if role == "doctor" and not license_number:
        return jsonify({"error": "Medical licence number is required"}), 400

    token = generate_verification_token()
    token_hash = hash_token(token)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=30)
    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (
                        full_name, email, password_hash, role,
                        email_verified,
                        email_verification_token_hash,
                        email_verification_expires_at
                    )
                    VALUES (%s, %s, %s, %s, FALSE, %s, %s)
                    RETURNING id
                    """,
                    (full_name, email, password_hash, role, token_hash, expiry)
                )

                user_id = cursor.fetchone()[0]

                if role == "patient":
                    cursor.execute(
                        "INSERT INTO patient_profiles (user_id) VALUES (%s)",
                        (user_id,)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO doctor_profiles (
                            user_id, specialization, license_number,
                            verification_status
                        )
                        VALUES (%s, %s, %s, 'pending')
                        """,
                        (user_id, specialization, license_number)
                    )

        verification_url = create_verification_url(token)
        send_verification_email(email, verification_url)

        return jsonify({
            "message": "Registration successful. Check your email to verify your account.",
            "email_verified": False
        }), 201

    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "Email or licence number already registered"}), 409

    except Exception:
        current_app.logger.exception("Registration failed")
        return jsonify({
            "error": "Registration could not be completed. Please try again."
        }), 500


@auth_bp.route("/verify-email", methods=["GET"])
def verify_email():
    token = request.args.get("token", "")

    if not token or len(token) > 200:
        return jsonify({
            "error": "Invalid verification link"
        }), 400

    token_hash = hash_token(token)

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET email_verified = TRUE,
                        email_verification_token_hash = NULL,
                        email_verification_expires_at = NULL
                    WHERE email_verification_token_hash = %s
                      AND email_verification_expires_at > NOW()
                      AND email_verified = FALSE
                    RETURNING id, role
                    """,
                    (token_hash,)
                )

                user = cursor.fetchone()

                if not user:
                    return jsonify({
                        "error": "Verification link is invalid or expired"
                    }), 400

        return jsonify({
            "message": "Email verified successfully!",
            "email_verified": True
        }), 200

    except Exception:
        current_app.logger.exception("Email verification failed")
        return jsonify({
            "error": "Verification could not be completed"
        }), 500
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not is_valid_email(email) or not password:
        return jsonify({"error": "Invalid email or password"}), 400

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, full_name, email, password_hash,
                           role, email_verified
                    FROM users
                    WHERE email = %s
                    """,
                    (email,)
                )
                user = cursor.fetchone()

        if not user or not check_password_hash(user[3], password):
            return jsonify({"error": "Invalid email or password"}), 401

        if not user[5]:
            return jsonify({
                "error": "Please verify your email before logging in."
            }), 403

        session.clear()
        session.permanent = True
        session["user_id"] = user[0]
        session["role"] = user[4]

        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user[0],
                "full_name": user[1],
                "email": user[2],
                "role": user[4]
            }
        }), 200

    except Exception:
        current_app.logger.exception("Login failed")
        return jsonify({"error": "Login could not be completed"}), 500
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    }), 200
@auth_bp.route("/csrf", methods=["GET"])
def get_csrf_token():
    return jsonify({
        "csrf_token": generate_csrf()
    }), 200