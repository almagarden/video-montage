from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Video Montage API"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 5
    
    # Database
    DATABASE_URL: str = "sqlite:///./video_montage.db"
    
    # Storage
    STORAGE_DIR: str = "./storage"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 