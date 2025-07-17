"""
Configuration settings for the Mental Health Agent application.
Handles environment variables, logging, and application settings.
"""

import os
import logging
from typing import Optional, List
from pathlib import Path
from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Mental Health Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_PREFIX: str = "/api"
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://mental_health_user:mental_health_pass@localhost:5432/mental_health_db"
    )
    
    # ChromaDB
    CHROMADB_HOST: str = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT: int = int(os.getenv("CHROMADB_PORT", "8001"))
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # AI Models - OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

    # AI Models - Google Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "2000"))
    GEMINI_SAFETY_SETTINGS: str = os.getenv("GEMINI_SAFETY_SETTINGS", "high")

    # Healthcare Model Configuration
    SAGE_HEALTHCARE_MODE: bool = os.getenv("SAGE_HEALTHCARE_MODE", "true").lower() == "true"
    DEFAULT_HEALTHCARE_MODEL: str = os.getenv("DEFAULT_HEALTHCARE_MODEL", "gemini")  # Default to Gemini for healthcare
    MODEL_ROUTING_ENABLED: bool = os.getenv("MODEL_ROUTING_ENABLED", "true").lower() == "true"
    
    # File Paths
    DATA_DIR: Path = Path("data")
    CACHE_DIR: Path = DATA_DIR / "cache"
    USER_STORAGE_DIR: Path = DATA_DIR / "user_storage"
    INDEX_STORAGE_DIR: Path = DATA_DIR / "index_storage"
    INGESTION_STORAGE_DIR: Path = DATA_DIR / "ingestion_storage"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
    
    # Medical Safety
    MEDICAL_DISCLAIMER_ENABLED: bool = os.getenv("MEDICAL_DISCLAIMER_ENABLED", "true").lower() == "true"
    SAFETY_CHECK_ENABLED: bool = os.getenv("SAFETY_CHECK_ENABLED", "true").lower() == "true"
    
    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v):
        if not v and os.getenv("ENVIRONMENT", "development") == "production":
            raise ValueError("OPENAI_API_KEY is required in production")
        return v
    
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        if v == "your-secret-key-change-in-production" and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("JWT_SECRET_KEY must be changed in production")
        return v
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.DATA_DIR,
            self.CACHE_DIR,
            self.USER_STORAGE_DIR,
            self.INDEX_STORAGE_DIR,
            self.INGESTION_STORAGE_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Create directories on import
settings.create_directories()