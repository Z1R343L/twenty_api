"""Redis client module."""
from typing import AsyncIterator
from aioredis import Redis, create_redis_pool

async def init_redis_pool(host: str) -> AsyncIterator[Redis]:
    pool = await create_redis_pool(f"redis://{host}")
    yield pool
    pool.close()
    await pool.wait_closed()