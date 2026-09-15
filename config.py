import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Enforce strong secret key in production
    if os.environ.get('FLASK_ENV') == 'production' and SECRET_KEY == 'dev-secret-key-change-in-production':
        raise ValueError("CRITICAL: SECRET_KEY environment variable must be set in production mode!")

    # Normalize DATABASE_URL (handling Heroku/AWS postgres:// prefix to postgresql://)
    db_url = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "instance" / "subscription_tracker.db"}')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Production Cookie Security Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key-testing-only'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
