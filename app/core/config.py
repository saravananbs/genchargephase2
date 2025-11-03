# core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://saravanan:saravanan24@localhost/gencharge")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sivaji_vaila_jelabi")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 2
    OTP_EXPIRE_MINUTES: int = 5
    OTP_SECRET: str = os.getenv("OTP_SECRET", "pooriya_pongala")
    ALGORITHM: str = "HS256"

settings = Settings()