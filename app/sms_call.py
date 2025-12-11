import re
import asyncio
from functools import partial
from twilio.rest import Client

from app.loader import twilio_num, twilio_sid, twilio_token


def _get_client() -> Client:
    if not twilio_sid or not twilio_token or not twilio_num:
        raise RuntimeError('Не заданы необходимые параметры для звонка')
    return Client(twilio_sid, twilio_token)

def _make_call_sync(to_phone: str, text: str) -> str:
    client = _get_client()
    twiml = f'<Response><Say language="ru-RU" voice="alice">{text}</Say></Response>'

    call = client.calls.create(
        to=to_phone,
        from_=twilio_num,
        twiml=twiml,
    )
    return call.sid

async def send_call(to_phone: str, text: str) -> str:
    loop = asyncio.get_running_loop()
    call_sid = await loop.run_in_executor(None, partial(_make_call_sync, to_phone, text))
    return call_sid

def normalize_kz_e164(phone: str) -> str:
    p = re.sub(r"\D", "", phone or "")
    if not p:
        return ""
    if p.startswith("87"):
        p = "7" + p[1:]
    elif p.startswith("8"):
        p = "7" + p[1:]
    if not p.startswith("7"):
        pass
    return f"+{p}"

async def send_sms(phone: str, text: str) -> dict:
    to_number = normalize_kz_e164(phone)
    if not to_number:
        return {'error': 'bad_phone', 'detail': f'Неверный номер телефона: {phone!r}'}
    def _send_sync():
        client = Client(twilio_sid, twilio_token)
        message = client.messages.create(from_=twilio_num, to=to_number, body=text)
        return {'sid': message.sid, 'status': message.status, 'to': to_number, '_provider': 'twilio'}
    try:
        result = await asyncio.to_thread(_send_sync)
        return result
    except Exception as error:
        return {'error': 'exception', 'detail': repr(error), 'to': to_number, '_provider': 'twilio'}