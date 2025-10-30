import threading

import uvicorn
from fastapi import FastAPI
from bot.tg_main import start
from core.settings import config
from api.controller import router as api_router
app = FastAPI(
    title=config.APP_NAME,
    docs_url=config.SWAGGER_PREFIX if config.DOCS_UI_ENABLED else None,
    redoc_url=config.REDOC_PREFIX if config.DOCS_UI_ENABLED else None,
)

app.include_router(api_router)



if __name__ == "__main__":
    tg_bot_thread = threading.Thread(target=start, daemon=True)
    tg_bot_thread.start()
    uvicorn.run(app, host=config.HOST, port=config.PORT)