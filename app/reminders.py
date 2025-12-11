from datetime import datetime
from sqlalchemy import select

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.keyboards import main_menu_kb, delivery_kb
from app.database.db import AsyncSessionLocal
from app.database.models import Reminder
from app.loader import bot, scheduler
from app.sms_call import send_sms
from app.sms_call import send_call


class States(StatesGroup):
    title = State()
    text = State()
    recurrence_type = State()
    time_to_send = State()
    days_or_date = State()
    delivery_method = State()
    contact = State()

class HelpStates(StatesGroup):
    text = State()


async def send_reminder(rem_id: int):
    async with AsyncSessionLocal() as session:
        reminder = await session.get(Reminder, rem_id)
        if not reminder or not reminder.active:
            try:
                scheduler.remove_job(str(rem_id))
            except:
                pass
            return
        msg = f"🔔 <b>{reminder.title}</b>\n\n{reminder.text}"
        try:
            if reminder.delivery_method == "telegram":
                await bot.send_message(reminder.user_id, msg)
            elif reminder.delivery_method == "sms":
                result = await send_sms(reminder.contact, msg)
                print("send_sms result:", result)
            elif reminder.delivery_method == "call":
                if not reminder.contact:
                    print("Не указан номер телефона для звонка")
                else:
                    call_sid = await send_call(reminder.contact, f"{reminder.title}. {reminder.text}",)
                    print("Twilio Call SID:", call_sid)
            elif reminder.delivery_method == "whatsapp":
                from app.whatsapp import send_whatsapp_message
                if not reminder.contact:
                    print("Не указан номер телефона для WhatsApp")
                else:
                    ok = await send_whatsapp_message(reminder.contact, msg)
                    print("WhatsApp sent:", ok)
        except Exception as e:
            print(f"Ошибка при доставке напоминания: {e}")
        if reminder.recurrence_type == "once":
            reminder.active = False
            await session.commit()
            try:
                scheduler.remove_job(str(rem_id))
            except Exception:
                pass

async def schedule_reminder_job(reminder: Reminder):
    try:
        scheduler.remove_job(str(reminder.id))
    except :
        pass
    if not reminder.active:
        return
    try:
        hour, minute = map(int, reminder.time_to_send.split(":"))
    except:
        return
    try:
        if reminder.recurrence_type == "once" and reminder.specific_datetime:
            if reminder.specific_datetime <= datetime.now():
                return
            scheduler.add_job(send_reminder, trigger="date", run_date=reminder.specific_datetime, args=(reminder.id,), id=str(reminder.id),)
        elif reminder.recurrence_type == "daily":
            scheduler.add_job(send_reminder, trigger="cron", hour=hour, minute=minute, args=(reminder.id,), id=str(reminder.id),)
        elif reminder.recurrence_type == "weekly" and reminder.days_of_week:
            scheduler.add_job(send_reminder, trigger="cron", day_of_week=",".join(map(str, reminder.days_of_week)), hour=hour, minute=minute, args=(reminder.id,), id=str(reminder.id),)
        elif reminder.recurrence_type == "monthly" and reminder.day_of_month:
            scheduler.add_job(send_reminder, trigger="cron", day=reminder.day_of_month, hour=hour, minute=minute, args=(reminder.id,), id=str(reminder.id),)
    except Exception:
        print("Ошибка планирования")

async def restore_scheduled_jobs():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Reminder).where(Reminder.active == True))
        reminders = result.scalars().all()
    for r in reminders:
        await schedule_reminder_job(r)

async def ask_delivery(message: Message, state: FSMContext):
    await message.answer("📬 Выберите способ доставки:", reply_markup=delivery_kb())
    await state.set_state(States.delivery_method)

async def save_new_reminder(message_obj: Message, state: FSMContext, user_id: int):
    data = await state.get_data()
    recurrence_type = data.get("recurrence_type")
    specific_datetime = data.get("specific_datetime")
    time_to_send = data.get("time_to_send")
    if not time_to_send and specific_datetime:
        time_to_send = specific_datetime.strftime("%H:%M")
    async with AsyncSessionLocal() as session:
        reminder = Reminder(
            user_id=user_id,
            title=data.get("title", "").strip(),
            text=data.get("text", "").strip(),
            recurrence_type=recurrence_type,
            time_to_send=time_to_send,
            days_of_week=data.get("days_of_week"),
            day_of_month=data.get("day_of_month"),
            specific_datetime=specific_datetime,
            delivery_method=data.get("delivery_method", "telegram"),
            contact=data.get("contact"),
            active=True,)
        session.add(reminder)
        await session.commit()
        await session.refresh(reminder)
    await schedule_reminder_job(reminder)
    await message_obj.answer("✅ Напоминание успешно создано!", reply_markup=main_menu_kb())
    await state.clear()