import asyncio

from app.reminders import restore_scheduled_jobs
from app.database.db import init_db
from app.handler import register_message_handlers
from app.callback import register_callback_handlers
from app.loader import bot, scheduler, dp


async def main():
    await init_db()
    register_message_handlers(dp)
    register_callback_handlers(dp)
    scheduler.start()
    await restore_scheduled_jobs()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        print('Бот запущен')
        asyncio.run(main())
    except Exception as error:
        print('main.py error:', error)
