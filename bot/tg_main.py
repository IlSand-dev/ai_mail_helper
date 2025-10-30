import asyncio

from aiogram import Bot, Dispatcher
from bot.controller import router as bot_router
from core.settings import config
from integrations.repository import CredentialsProvider


async def start_bot():
    bot = Bot(token=config.TG_TOKEN)
    dp = Dispatcher(credentials_provider=CredentialsProvider)
    dp.include_router(bot_router)

    await dp.start_polling(bot)

def start():
    asyncio.run(start_bot())