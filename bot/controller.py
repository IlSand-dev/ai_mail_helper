from urllib.parse import urlencode

from aiogram import Router, types
from aiogram.filters import Command

from core.settings import config
from integrations.repository import CredentialsProvider

router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я помогаю работать с электронной почтой!")

@router.message(Command("login"))
async def login_cmd(message: types.Message):
    telegram_id = str(message.from_user.id)

    login_url = f"{config.HOST}/login?{urlencode({'telegram_id': telegram_id})}"
    await message.answer(f"Нажмите на ссылку чтобы подключить Google:\n\n{login_url}")

@router.message(Command("get_credentials"))
async def logout_cmd(message: types.Message, credentials_provider: CredentialsProvider):
    telegram_id = str(message.from_user.id)
    credentials = await credentials_provider.get_credentials(telegram_id)
    await message.answer(str(credentials))