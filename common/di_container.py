from integrations.db_connection_provider import RedisConnectionProvider


class DIContainer:
    redis_connection_provider: RedisConnectionProvider

    def register_redis(self, connection_provider: type[RedisConnectionProvider]):
        self.redis_connection_provider = connection_provider()

di = DIContainer()