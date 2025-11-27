import asyncio

from aiogram import Bot, Dispatcher
from bot.controller import router as bot_router
from core.lifespan import lifespan
from core.settings import config
from integrations.repository import CredentialsProvider


async def start_bot():
    async with lifespan():
        print("Starting bot")
        bot = Bot(token=config.TG_TOKEN)
        dp = Dispatcher(credentials_provider=CredentialsProvider())
        dp.include_router(bot_router)
        print("Bot started")
        await dp.start_polling(bot)