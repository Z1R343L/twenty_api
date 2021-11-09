"""Containers module."""
from dependency_injector import containers, providers
from . import redis, services


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    redis_pool = providers.Resource(redis.init_redis_pool, host=config.redis_host)
    service = providers.Factory(services.Redis, redis=redis_pool)
