# backend/app/config.py - FIXED VERSION
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/investment_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Zerodha API Configuration
    ZERODHA_API_KEY: str = "femohcxeam7tjt1p"
    ZERODHA_API_SECRET: str = "xjudlehzrnblhs1wznjvb95uhgtny54f"
    ZERODHA_USER_ID: str = "MSC739"
    ZERODHA_PASSWORD: str = "Pranjal@1006"
    ZERODHA_TOTP_KEY: str = "PHHXNLG7ZPS3C4GCOF7HLGCM7DV6HRAB"
    ZERODHA_ACCESS_TOKEN_FILE: str = "zerodha_access_token.txt"
    ZERODHA_REDIRECT_URL: str = "http://localhost:8000/auth/callback"
    
    # Security Configuration
    JWT_SECRET: str = "your_super_secret_jwt_key_change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Portfolio Configuration
    MIN_INVESTMENT: int = 200000
    TARGET_ALLOCATION: float = 5.00
    MIN_ALLOCATION: float = 4.00
    MAX_ALLOCATION: float = 7.00
    REBALANCING_THRESHOLD: int = 10000
    
    # Market Hours
    MARKET_OPEN_TIME: str = "09:15"
    MARKET_CLOSE_TIME: str = "15:30"
    
    # Frontend Configuration
    API_BASE_URL: str = "http://localhost:8000/api"
    FRONTEND_PORT: int = 8501
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create the settings instance that will be imported
settings = Settings()