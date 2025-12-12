import re
from datetime import datetime
from sqlalchemy import update

from aiogram import F, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.keyboards import reply_kb, main_menu_kb, recurrence_kb, help_kb, help_kb_back
from app.database.db import AsyncSessionLocal
from app.database.models import Reminder, Help
from app.reminders import States, ask_delivery, save_new_reminder, HelpStates


async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добро пожаловать в бот напоминаний!", reply_markup=reply_kb(),)
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

async def show_main_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

async def about(message: Message):
    await message.answer("💭 О боте\n Этот бот создан для заботы о самом важном - о вас и вашем времени. Бот помогает не забывать о том, что действительно важно: принять таблетки, выпить воду, лечь спать вовремя, не забыть про встречу или просто сделать паузу.\n Всё просто: напишите название и текст напоминания, укажите время и дату, выберите, куда его доставить - в Telegram, WhatsApp, SMS или Звонком.\n И в нужный момент бот напомнит вам о ваших делах - в том мессенджере, где вам удобно.\n Это не просто напоминания – это способ взять под контроль свой день, здоровье и привычки, не тратя лишнего внимания. Мы верим, что забота начинается с мелочей - и иногда одно вовремя сказанное «пора» делает день лучше")

async def help_menu(message: Message):
    await message.answer("Выберите свой вариан:", reply_markup=help_kb())

async def save_help_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    contact = message.from_user.username
    if not text:
        await message.answer("Пожалуйста, опишите свою проблему текстом")
        return
    async with AsyncSessionLocal() as session:
        help_record = Help(
            user_id=user_id,
            text=text,
            recurrence_type="help",   
            contact = message.from_user.username)
        session.add(help_record)
        await session.commit()
    await message.answer("✅Спасибо! Ваша заявка сохранена, мы свяжемся с вами позже", reply_markup=help_kb_back())
    await state.clear()

async def process_title(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("mode") == "edit" and data.get("edit_field") == "title":
        rem_id = data.get("rem_id")
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Reminder).where(Reminder.id == rem_id).values(
                    title=message.text.strip()))
            await session.commit()
        await message.answer("✅Название изменено!", reply_markup=main_menu_kb())
        await state.clear()
        return
    await state.update_data(title=message.text.strip())
    await message.answer("✏️ Введите текст напоминания:")
    await state.set_state(States.text)

async def process_text(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("mode") == "edit" and data.get("edit_field") == "text":
        rem_id = data.get("rem_id")
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Reminder).where(Reminder.id == rem_id).values(
                    text=message.text.strip()))
            await session.commit()
        await message.answer("✅Текст изменен!", reply_markup=main_menu_kb())
        await state.clear()
        return
    await state.update_data(text=message.text.strip())
    await message.answer("🔄Выберите тип повторения:", reply_markup=recurrence_kb())
    await state.set_state(States.recurrence_type)

async def process_time(message: Message, state: FSMContext):
    text = message.text or ''
    if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', text):
        await message.answer("Неверный формат времени. Пример: 14:30")
        return
    await state.update_data(time_to_send=text)
    data = await state.get_data()
    rtype = data.get("recurrence_type")
    # if rtype == "once":
    #     try:
    #         dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
    #         if dt <= datetime.now():
    #             await message.answer("Дата должна быть в будущем")
    #             return
    #         await state.update_data(
    #             specific_datetime=dt,
    #             time_to_send=dt.strftime("%H:%M"),
    #         )
    #     except:
    #         await message.answer("Неверный формат. Пример: 2025-12-31 14:30")
    #         return
    if rtype == "weekly":
        await message.answer("📅 Введите дни недели через запятую (1=Пн ... 7=Вс):\n Пример: 1, 5 (Понедельник и Пятница)")
        await state.set_state(States.days_or_date)
        return
    if rtype == "monthly":
        await message.answer("📅 Введите день месяца (1-31):")
        await state.set_state(States.days_or_date)
        return
    await ask_delivery(message, state)

async def process_days_or_date(message: Message, state: FSMContext):
    data = await state.get_data()
    rtype = data.get("recurrence_type")
    text = (message.text or "").strip()
    if rtype == "once":
        try:
            dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
            if dt <= datetime.now():
                await message.answer("Дата должна быть в будущем")
                return
            await state.update_data(specific_datetime=dt)
        except Exception:
            await message.answer("Неверный формат. Пример: 2025-12-31 14:30")
            return
    elif rtype == "weekly": 
        try:
            days = [int(x.strip()) for x in text.split(",") if x.strip().isdigit()]
            if not days or not all(1 <= d <= 7 for d in days):
                raise ValueError
            days0 = [(d - 1) for d in days]
            await state.update_data(days_of_week=days0)
            await state.update_data(days_of_week=days)
        except Exception:
            await message.answer("Введите числа от 1 до 7 через запятую")
            return
    elif rtype == "monthly":
        try:
            day = int(text)
            if not 1 <= day <= 31:
                raise ValueError
            await state.update_data(day_of_month=day)
        except Exception:
            await message.answer("Введите число от 1 до 31")
            return
    await ask_delivery(message, state)

async def process_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text.strip())
    await save_new_reminder(message, state, message.from_user.id)

def register_message_handlers(dp: Dispatcher):
    dp.message.register(start, CommandStart())
    dp.message.register(show_main_menu, F.text == "🏠Главное меню")
    dp.message.register(about, F.text == "💭О боте")
    dp.message.register(help_menu, F.text == "🫂Помощь")
    dp.message.register(process_title, States.title)
    dp.message.register(process_text, States.text)
    dp.message.register(process_time, States.time_to_send)
    dp.message.register(process_days_or_date, States.days_or_date)
    dp.message.register(process_contact, States.contact)
    dp.message.register(save_help_message, HelpStates.text)