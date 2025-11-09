from redis.asyncio import from_url
from ..core.config import settings

async def get_redis():
    return from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
