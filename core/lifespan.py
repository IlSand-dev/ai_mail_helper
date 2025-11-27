from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.di_container import di
from integrations.db_connection_provider import RedisConnectionProvider


@asynccontextmanager
async def lifespan(_app: FastAPI=None):
    di.register_redis(RedisConnectionProvider)
    yield
    await di.redis_connection_provider.close_connection_pool()
