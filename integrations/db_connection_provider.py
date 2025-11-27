from redis.asyncio import BlockingConnectionPool, Redis

from core.settings import config

class RedisConnectionProvider:

    def __init__(self):
        self._pool: BlockingConnectionPool = BlockingConnectionPool(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            username=config.REDIS_USER,
            password=config.REDIS_PASSWORD,
            max_connections=15,
            timeout=3,
            decode_responses=True
        )

    async def get_connection(self) -> Redis:
        conn: Redis = Redis.from_pool(connection_pool=self._pool)
        conn.auto_close_connection_pool = False
        return conn

    async def close_connection_pool(self):
        await self._pool.aclose()
