import base64
import pprint
import traceback
from urllib.parse import urlencode

import aiohttp
from aiogram import Router, types
from aiogram.filters import Command

from core.settings import config
from integrations.repository import CredentialsProvider
from googleapiclient.discovery import build


router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я помогаю работать с электронной почтой!")

@router.message(Command("login"))
async def login_cmd(message: types.Message):
    telegram_id = str(message.from_user.id)

    login_url = f"{config.BASE_URL}login?{urlencode({'telegram_id': telegram_id})}"
    await message.answer(f"Нажмите на ссылку чтобы подключить Google:\n\n{login_url}")

@router.message(Command("get_mail"))
async def get_mail_cmd(message: types.Message, credentials_provider: CredentialsProvider):
    user_id = str(message.from_user.id)
    credentials = await credentials_provider.get_credentials(user_id)
    try:
        service = build('gmail', 'v1', credentials=credentials)

        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])
        if not messages:
            await message.answer("Похоже, у Вас нет писем.")
            return

        out = []

        for i, m in enumerate(messages):
            msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
            if i == 1:
                pprint.pprint(msg.get('payload', {}))
            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(без темы)')
            snippet = msg.get('snippet', '')
            out.append(f"{i+1}) {subject}\n{snippet}")
        reply = "Последние письма:\n\n" + "\n".join(out)
        await message.answer(reply)
    except Exception as e:
        print(traceback.format_exc())
        await message.answer('Ошибка при получении писем')


@router.message(Command("summarize_email_short"))
async def summarize_email_short(message: types.Message, credentials_provider: CredentialsProvider):
    user_id = str(message.from_user.id)
    credentials = await credentials_provider.get_credentials(user_id)
    try:
        service = build('gmail', 'v1', credentials=credentials)
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        if not messages:
            await message.answer("Похоже, у Вас нет писем.")
            return
        msg = messages[0]
        msg_id = msg['id']
        msg_thread_id = msg['threadId'] if 'threadId' in msg else None
        msg = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(без темы)')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(отправитель неизвестен)')
        labels = msg.get('labelIds')
        payload = msg.get('payload')
        bodies = [part['body']['data'] for part in payload['parts'] if part.get('mimeType') in ('text/plain', 'text/html')]
        bodies = [base64.urlsafe_b64decode(body.encode('utf-8')) for body in bodies]
        decoded_bodies = []
        for i, b in enumerate(bodies):
            decoded_bodies.append(b.decode('utf-8'))


        body = {
            'email': {
                'id': msg_id,
                'thread_id': msg_thread_id,
                'sender': sender,
                'subject': subject,
                'body': "\n".join(decoded_bodies),
                'labels': labels
            },
            'short': True
        }

        await message.answer("Ожидайте")
        async with aiohttp.ClientSession() as session:
            async with session.post(config.AI_HOST + '/summarize/email', json=body, ssl=False) as resp:
                await message.answer(await resp.text())

    except Exception as e:
        print(traceback.format_exc())
        await message.answer('Ошибка при получении писем')