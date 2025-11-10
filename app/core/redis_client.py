from redis.asyncio import from_url
from ..core.config import settings

async def get_redis():
    """
    Get async Redis client connection.

    Creates and returns an async Redis connection using the configured Redis URL.
    Enables UTF-8 encoding with decoded responses for convenient data handling.

    Returns:
        aioredis.Redis: Async Redis client instance ready for cache operations.
    """
    return from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
