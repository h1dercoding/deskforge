import redis.asyncio as redis
from src.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    return redis_client


async def close_redis() -> None:
    await redis_client.close()
