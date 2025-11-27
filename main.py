from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from bot.tg_main import start_bot
import asyncio

from core.lifespan import lifespan
from core.settings import config
from api.controller import router as api_router

app = FastAPI(
    title=config.APP_NAME,
    docs_url=config.SWAGGER_PREFIX if config.DOCS_UI_ENABLED else None,
    redoc_url=config.REDOC_PREFIX if config.DOCS_UI_ENABLED else None,
    lifespan=lifespan
)

app.include_router(api_router)


async def main():
    bot_task = asyncio.create_task(start_bot())
    server = uvicorn.Server(
        uvicorn.Config(app, host=config.HOST, port=config.PORT)
    )
    await asyncio.gather(bot_task, server.serve())

if __name__ == "__main__":
    asyncio.run(main())