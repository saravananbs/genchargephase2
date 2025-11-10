import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.

    Centralized configuration for database, authentication, and third-party service connections.

    Attributes:
        DATABASE_URL (str): PostgreSQL connection string.
        SECRET_KEY (str): Secret key for JWT token signing.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): JWT access token expiration time in minutes (default: 1).
        REFRESH_TOKEN_EXPIRE_DAYS (int): Refresh token expiration time in days (default: 2).
        OTP_EXPIRE_MINUTES (int): OTP validity duration in minutes (default: 5).
        OTP_SECRET (str): Secret key for OTP generation.
        ALGORITHM (str): JWT signing algorithm (e.g., HS256).
        MONGO_URL (str): MongoDB connection string.
        MONGO_DB_NAME (str): MongoDB database name.
        POSTGRES_USER (str): PostgreSQL username.
        POSTGRES_PASSWORD (str): PostgreSQL password.
        REDIS_URL (str): Redis server connection string.
    """
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