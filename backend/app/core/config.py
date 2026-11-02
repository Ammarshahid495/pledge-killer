"""
Application Configuration Settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import email_validator

# Disable DNS deliverability checks so email validation is instantaneous and doesn't block on network
email_validator.CHECK_DELIVERABILITY = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Pledge Fighter"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-pledge-fighter-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Database
    # Defaults to SQLite for immediate local zero-dependency testing, can be overridden with Postgres URL
    DATABASE_URL: str = "sqlite:///./pledge_fighter.db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    LOCAL_STORAGE_DIR: str = "./storage_uploads"
    S3_ENDPOINT: Optional[str] = None
    S3_BUCKET: str = "pledge-fighter-submissions"
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Analysis Threshold
    MIN_SUBMISSION_THRESHOLD: int = 5


settings = Settings()

# Ensure local storage directory exists
if settings.STORAGE_TYPE == "local":
    os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
