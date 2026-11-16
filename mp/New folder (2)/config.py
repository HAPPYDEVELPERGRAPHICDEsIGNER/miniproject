"""
Configuration loader and validator for SmartEdu AI Learning Platform.
Safely loads environment variables without exposing sensitive credentials.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

class AppSettings:
    """Application settings with secure credential accessors."""
    
    # General
    APP_NAME: str = os.getenv("APP_NAME", "SmartEdu AI Learning Platform")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "college-smartedu-secret-key-change-in-production-2026-secure")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'database' / 'platform.db'}")
    
    # AI Assistant
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or None
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY") or None
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Code Execution (Judge0)
    JUDGE0_API_URL: str = os.getenv("JUDGE0_API_URL", "https://judge0-ce.p.rapidapi.com")
    JUDGE0_API_KEY: Optional[str] = os.getenv("JUDGE0_API_KEY") or None
    JUDGE0_API_HOST: str = os.getenv("JUDGE0_API_HOST", "judge0-ce.p.rapidapi.com")
    
    # Initial Admin
    ADMIN_INITIAL_EMAIL: str = os.getenv("ADMIN_INITIAL_EMAIL", "admin@smartedu.edu")
    ADMIN_INITIAL_PASSWORD: str = os.getenv("ADMIN_INITIAL_PASSWORD", "Admin@SecurePass2026")

    @classmethod
    def is_ai_configured(cls) -> bool:
        if cls.AI_PROVIDER == "gemini" and cls.GEMINI_API_KEY:
            return True
        if cls.AI_PROVIDER == "openai" and cls.OPENAI_API_KEY:
            return True
        return False

    @classmethod
    def is_judge0_configured(cls) -> bool:
        # Check if RapidAPI key or custom self-hosted endpoint is provided
        if "rapidapi.com" in cls.JUDGE0_API_URL:
            return bool(cls.JUDGE0_API_KEY and len(cls.JUDGE0_API_KEY.strip()) > 5)
        # Self-hosted Judge0 instance doesn't strictly mandate RapidAPI key
        return bool(cls.JUDGE0_API_URL and not "rapidapi.com" in cls.JUDGE0_API_URL)

    @classmethod
    def get_public_integrations_status(cls) -> Dict[str, Any]:
        """Provides frontend diagnostic status without revealing actual keys."""
        return {
            "ai_configured": cls.is_ai_configured(),
            "ai_provider": cls.AI_PROVIDER,
            "ai_model": cls.GEMINI_MODEL if cls.AI_PROVIDER == "gemini" else cls.OPENAI_MODEL,
            "judge0_configured": cls.is_judge0_configured(),
            "judge0_endpoint": cls.JUDGE0_API_URL,
            "database_type": "PostgreSQL" if "postgresql" in cls.DATABASE_URL else "SQLite",
            "app_version": "2.0.0"
        }

settings = AppSettings()
