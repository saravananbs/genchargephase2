# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from typing import AsyncGenerator

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.MONGO_DB_NAME]

async def get_mongo_db() -> AsyncGenerator:
    """
    Async MongoDB database connection dependency for FastAPI route handlers.

    Yields the configured MongoDB database instance for route use.
    Provides async context management for Motor (async MongoDB driver).

    Yields:
        AsyncIOMotorDatabase: Active MongoDB database instance.
    """
    try:
        yield db
    finally:
        pass

