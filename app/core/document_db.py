# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from typing import AsyncGenerator

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.MONGO_DB_NAME]

async def get_mongo_db() -> AsyncGenerator:
    try:
        yield db
    finally:
        pass

async def init_counters():
    await db.counters.update_one(
        {"_id": "notification_id"},
        {"$setOnInsert": {"seq": 0}},
        upsert=True
    )