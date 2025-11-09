import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 2
    OTP_EXPIRE_MINUTES: int = 5
    OTP_SECRET: str = os.getenv("OTP_SECRET")
    ALGORITHM: str = os.getenv("ALGORITHM")
    MONGO_URL: str = os.getenv("MONGO_URL")
    MONGO_DB_NAME: str  = os.getenv("MONGO_DB_NAME")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    REDIS_URL: str = os.getenv("REDIS_URL")

settings = Settings()