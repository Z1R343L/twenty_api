import dill as pickle
import aioredis

class Redis:
    """
    [aioredis instance]
    """
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def get(self, key: str, dill: bool = True):
        data = await self._redis.get(key)
        if dill:
            return pickle.loads(data)
        else:
            return data

    async def set(self, key: str, data, dill: bool = True) -> None:
        if dill:
            data = pickle.dumps(data)
        await self._redis.set(key, data)

    async def exists(self, key: str):
        return await self._redis.exists(key)

    async def get_by_prefix(self, prefix: str) -> dict:
        keys = await self._redis.keys(pattern=f"{prefix}*")
        res = {}
        for key in keys:
            res.update(pickle.loads(await self._redis.get(key)))
        return res
