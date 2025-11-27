import json

from google.oauth2.credentials import Credentials

from common.di_container import di
from integrations.db_connection_provider import RedisConnectionProvider


class CredentialsProvider:
    redis_adapter: RedisConnectionProvider

    def __init__(self):
        self.redis_adapter = di.redis_connection_provider

    async def get_credentials(self, user_id):
        async with await self.redis_adapter.get_connection() as redis_con:
            data = await redis_con.hgetall(f"user_id:{user_id}")
        creds = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=json.loads(data.get("scopes"))
        )
        return creds

    async def save_credentials(self, user_id, creds, ):
        data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": json.dumps(creds.scopes)
        }
        print(data)
        async with await self.redis_adapter.get_connection() as redis_con:
            await redis_con.hset(f"user_id:{user_id}", mapping=data)

    async def delete_credentials_for_user(self, user_id: int):
        async with await self.redis_adapter.get_connection() as redis_con:
            await redis_con.delete(f"user_id:{user_id}")