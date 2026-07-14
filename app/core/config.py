import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    REDIS_URL: str = "redis://localhost:6379/0"

    R2_ACCOUNT_ID: str = "mock-account-id"
    R2_ACCESS_KEY_ID: str = "mock-access-key"
    R2_SECRET_ACCESS_KEY: str = "mock-secret-key"
    R2_BUCKET_NAME: str = "lynk-transfers"

    MAX_FILES_PER_TRANSFER: int = 10
    MAX_INDIVIDUAL_FILE_SIZE: int = 52428800
    MAX_TOTAL_TRANSFER_SIZE: int = 524288000
    
    TRANSFER_LIFETIME_SECONDS: int = 1800
    RECEIVER_SESSION_LIFETIME_SECONDS: int = 600
    UPLOAD_URL_LIFETIME_SECONDS: int = 900
    DOWNLOAD_URL_LIFETIME_SECONDS: int = 300

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()