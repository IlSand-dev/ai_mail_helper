from typing import Annotated

from fastapi import APIRouter, Depends, Request
from google_auth_oauthlib.flow import Flow
from starlette.responses import RedirectResponse, HTMLResponse

from core.settings import config
from integrations.repository import CredentialsProvider

router = APIRouter(prefix='', tags=['OAUTH2'])


@router.get("/login")
async def login(telegram_id: int):
    """
    Альтернативная точка, если хотите вручную открыть ссылку:
    /login?telegram_id=12345678
    """
    flow = Flow.from_client_secrets_file(
        config.GMAIL_MAIN_CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        redirect_uri=f'{config.BASE_URL}oauth2callback',
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(telegram_id),
        prompt="consent",
    )
    print(auth_url)
    return RedirectResponse(auth_url)


@router.get("/oauth2callback")
async def oauth2_callback(
        credentials_provider: Annotated[CredentialsProvider, Depends(CredentialsProvider)],
        request: Request,
        state: str = None,
        code: str = None,
        error: str = None,
):
    if not state or not code:
        print(f'{error=}')
        return HTMLResponse("<h3>Missing state or code</h3>", status_code=400)
    telegram_id = state
    flow = Flow.from_client_secrets_file(
        config.GMAIL_MAIN_CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        redirect_uri=f'{config.BASE_URL}oauth2callback',
    )
    print(f'{request.url=}')
    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials
    await credentials_provider.save_credentials(telegram_id, creds)
    return HTMLResponse("<h3>Authentication successful</h3><p>You can close this page and return to Telegram.</p>")
