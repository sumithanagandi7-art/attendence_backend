import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_db_url(url):
    """
    Render/Heroku-style hosts hand out URLs starting with 'postgres://', but
    modern SQLAlchemy requires 'postgresql://'. Normalize automatically so
    deployment doesn't silently fail on this one-character difference.
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    # --- DBMS configuration ---
    # Default: SQLite (zero-setup, file-based DBMS) for local development.
    # In production (Render, Railway, etc.), set the DATABASE_URL environment
    # variable to a real client-server DBMS connection string, e.g.:
    #   PostgreSQL: postgresql://user:password@host:5432/smartgov
    #   MySQL:      mysql+pymysql://user:password@host:3306/smartgov
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL")
    ) or f"sqlite:///{os.path.join(BASE_DIR, 'smartgov.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Security ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-secret-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    # --- Face recognition ---
    FACE_MATCH_TOLERANCE = 0.5  # lower = stricter match (0.4-0.6 typical)
    FACE_UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "faces")

    # --- Geofencing ---
    DEFAULT_GEOFENCE_RADIUS_METERS = 200
