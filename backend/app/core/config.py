import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

# Load .env file if it exists (for local development outside Docker)
# This allows you to set environment variables in a .env file for local testing
# without modifying the Docker environment directly.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "BakeMate"

    # APP_FILES_DIR: str = os.getenv("APP_FILES_DIR", "/app/app_files") # For Docker
    APP_FILES_DIR: str = os.getenv("APP_FILES_DIR", "./app_files") # For local development

    # Database
    # The DATABASE_URL will be taken from the environment variable set in docker-compose.yml
    # For local development without Docker, it can fall back to a default or be set in a .env file.
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{APP_FILES_DIR}/bakemate_dev.db")

    # Airtable - ensure these are set in your environment (e.g., .env file or Docker env)
    AIRTABLE_BASE_ID: str = os.getenv("AIRTABLE_BASE_ID", "YOUR_AIRTABLE_BASE_ID_HERE")
    AIRTABLE_API_KEY: str = os.getenv("AIRTABLE_API_KEY", "YOUR_AIRTABLE_API_KEY_HERE")
    # Placeholder for table names if they are consistent, otherwise pass to repository
    # AIRTABLE_INGREDIENTS_TABLE_NAME: str = "Ingredients"

    # SendGrid - ensure these are set
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "YOUR_SENDGRID_API_KEY_HERE")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@example.com")
    # Example: For email verification or other transactional emails
    # EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "a_super_secret_key_for_jwt_please_change_this")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    # Access token lifetime in minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")) # e.g., 60 minutes
    # SECURE_COOKIE_NAME: str = "bakemate_auth"

    # CORS (Cross-Origin Resource Sharing)
    # BACKEND_CORS_ORIGINS: list[str] = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(',')

    # Default user settings (example)
    # DEFAULT_USER_HOURLY_RATE: float = 25.0
    # DEFAULT_USER_OVERHEAD_PER_MONTH: float = 100.0

    model_config = ConfigDict(case_sensitive=True)
        # If you have a .env file in the root of your project (alongside docker-compose.yml)
        # and want pydantic-settings to load it automatically when not in Docker, you can specify:
        # env_file = ".env"
        # env_file_encoding = "utf-8"

settings = Settings()

