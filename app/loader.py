import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
load_dotenv()


db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("Нет ссылки на бд")

token = os.getenv("TOKEN")
if not token:
    print("Токена нет")

twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
if not twilio_sid:
    print("Нет сида для звонка")

twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
if not twilio_token:
    print("Нет токена для звонка")

twilio_num = os.getenv("TWILIO_FROM_NUMBER")
if not twilio_num:
    print("Нет номера для звонка")

w_id = os.getenv("ULTRAMSG_INSTANCE_ID")
if not w_id:
    print("Нет айди для ватсапа")

w_token = os.getenv("ULTRAMSG_TOKEN")
if not w_token:
    print("Нет токена для ватсапа")

w_url = os.getenv("ULTRAMSG_BASE_URL")
if not w_url:
    print('Нет ссылки для ватсапа')

bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()