import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from app.loader import w_token, w_url


async def send_whatsapp_message(phone_number: str, text: str) -> bool:
    if not w_url or not w_token:
        print("UltraMsg config missing: w_url or w_token")
        return False
    url = f"{w_url.rstrip('/')}/messages/chat"
    payload = {
        "token": w_token,
        "to": phone_number,
        "body": text,
    }
    timeout = ClientTimeout(total=15)
    connector = TCPConnector(ssl=False)
    try:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.post(url, data=payload) as resp:
                raw_text = await resp.text()
                data = None
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = {"raw": raw_text}
                print("UltraMsg status:", resp.status)
                print("UltraMsg response:", data)
                if resp.status >= 400:
                    return False
                if isinstance(data, dict):
                    if data.get("sent") is True:
                        return True
                    if data.get("error"):
                        return False
                    return True
                return True
    except Exception as e:
        print("Ошибка при запросе к UltraMsg:", repr(e))
        return False