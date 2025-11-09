import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://saravanan:saravanan24@localhost/genchargetesting")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sivaji_vaila_jelabi")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 2
    OTP_EXPIRE_MINUTES: int = 5
    OTP_SECRET: str = os.getenv("OTP_SECRET", "pooriya_pongala")
    ALGORITHM: str = "HS256"
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    MONGO_DB_NAME: str  = os.getenv("MONGO_DB_NAME", "genchargetesting")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "saravanan")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "saravanan24")

settings = Settings()