import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Configuration
    APP_NAME: str = "AuraAI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/aura_ai"

    # Security & JWT Configuration
    JWT_SECRET_KEY: str = "aura_ai_super_secret_development_key_32bytes_min!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Provider Configuration
    AI_PROVIDER: str = "groq"
    AI_MODEL: str = "llama-3.3-70b-versatile"
    AI_API_KEY: str = ""

    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 20
    UPLOAD_DIR: str = "uploads"

    # CORS Settings
    CORS_ORIGINS: str = "http://127.0.0.1:8000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
