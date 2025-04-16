import os
from typing import List, Union, Optional
from pydantic import PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Base settings
    APP_NAME: str = "analisaai-sync"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:4200", "https://analisaai.com"]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/analisaai")
    
    # Redis and Celery settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Apify settings
    APIFY_API_TOKEN: str = os.getenv("APIFY_API_TOKEN", "")
    
    # Encryption settings for social tokens
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # Rate limiting settings
    RATE_LIMIT_PER_SECOND: int = 5
    
    # Third-party API settings
    APIFY_BASE_URL: str = "https://api.apify.com/v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Initialize settings object
settings = Settings()