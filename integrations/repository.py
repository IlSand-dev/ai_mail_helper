import json
import os
import pathlib

from google.oauth2.credentials import Credentials

from core.settings import config


class CredentialsProvider:

    def __init__(self):
        self.TOKENS = pathlib.Path(config.TOKENS_DIR)
        self.TOKENS.mkdir(exist_ok=True)

    def _token_path(self, user_id):
        return str(self.TOKENS / f"{user_id}.json")

    async def get_credentials(self, user_id):
        path = self._token_path(user_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            data = json.load(f)
        creds = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes")
        )
        return creds

    async def save_credentials(self, user_id, creds):
        data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }
        with open(self._token_path(user_id), "w") as f:
            json.dump(data, f)

    async def delete_credentials_for_user(self, user_id: int):
        p = self._token_path(user_id)
        if os.path.exists(p):
            os.remove(p)