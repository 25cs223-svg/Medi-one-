from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
from flask import Flask, jsonify
from app.extensions import limiter
from app.database import get_db_connection

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.getenv("SESSION_SECRET"),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=1800
)

csrf = CSRFProtect(app)

limiter.init_app(app)

from app.routes.auth import auth_bp
from app.routes.patient_risk import patient_risk_bp

app.register_blueprint(auth_bp)
app.register_blueprint(patient_risk_bp)

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