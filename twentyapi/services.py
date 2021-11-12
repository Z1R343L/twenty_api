import aioredis
import srsly

class Redis:
    def __init__(self, redis: aioredis.Redis) -> None:
        """[aioredis instance]"""
        self._redis = redis

    async def get(self, key: str) -> dict:
        return srsly.msgpack.loads(await self._redis.get(key))

    async def set(self, key: str, data: dict) -> None:
        await self._redis.set(key, srsly.msgpack_dumps(data))

    async def exists(self, key: str):
        return await self._redis.exists(key)

    async def get_by_prefix(self, prefix: str) -> dict:
        keys = await self._redis.keys(pattern=f"{prefix}*")
        res = {}
        for key in keys:
            res.update(srsly.msgpack_loads(await self._redis.get(key)))
        return res
