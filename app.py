from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
import psycopg
from flask import Flask, jsonify

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.getenv("SESSION_SECRET"),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=1800
)

csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return psycopg.connect(database_url, connect_timeout=10)


@app.route("/")
def home():
    return jsonify({
        "project": "Medi-One",
        "message": "AI Medical Management Portal",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "backend": "Flask"
    })


@app.route("/db-health")
def database_health():
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]

        return jsonify({
            "status": "connected",
            "database": "PostgreSQL",
            "message": "Cloud database connection successful"
        })

    except Exception:
        app.logger.exception("Database health check failed")
        return jsonify({
            "status": "error",
            "message": "Database connection failed. Check server configuration."
        }), 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )