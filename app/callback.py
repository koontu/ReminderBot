from sqlalchemy import select, delete

from aiogram import F, Dispatcher
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.keyboards import main_menu_kb, add_new_menu_kb, add_name
from app.database.db import AsyncSessionLocal
from app.database.models import Reminder
from app.reminders import States, save_new_reminder, HelpStates


QUICK_TITLES = {
    "name_med": "💊 Таблетки",
    "name_aqua": "💦 Вода",
    "name_zzz": "💤 Сон",
}

async def quick_title(callback: CallbackQuery, state: FSMContext):
    title = QUICK_TITLES.get(callback.data)
    if not title:
        await callback.answer()
        return

    await state.update_data(title=title)
    await callback.message.edit_text("✍️ Введите текст напоминания:")
    await state.set_state(States.text)
    await callback.answer()

async def help(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('✍🏻Опишите свою проблему:')
    await state.set_state(HelpStates.text)
    await callback.answer()

async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb())
    await callback.answer()

async def add_new(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("📝 Введите <b>название</b> напоминания:\nИли выберите из предложенных:", reply_markup=add_name())
    await state.set_state(States.title)
    await callback.answer()

async def process_rec_type(callback: CallbackQuery, state: FSMContext):
    rec_type = callback.data.replace("rec_", "")
    await state.update_data(recurrence_type=rec_type)
    if rec_type == "once":
        await callback.message.edit_text("📅 Введите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ)\nНапример: 2025-12-31 14:30")
        await state.set_state(States.days_or_date)
    else:
        await callback.message.edit_text("⏰ Введите время в формате ЧЧ:ММ (например 14:30):")
        await state.set_state(States.time_to_send)
    await callback.answer()

async def process_delivery(callback: CallbackQuery, state: FSMContext):
    method = callback.data.replace("del_", "")
    await state.update_data(delivery_method=method)
    labels = {
        "telegram": "Telegram",
        "whatsapp": "WhatsApp",
        "sms": "SMS",
        "call": "звонка",
    }
    if method == "telegram":
        await state.update_data(contact=None)
        await save_new_reminder(callback.message, state, callback.from_user.id)
    else:
        label = labels.get(method, method)
        await callback.message.edit_text(
            f"📞 Введите номер телефона для {label} (например: 77011234567):"
        )
        await state.set_state(States.contact)
    await callback.answer()

async def view_active(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Reminder).where(Reminder.user_id == callback.from_user.id, Reminder.active == True).order_by(Reminder.id.desc()))
        reminders = result.scalars().all()
    if not reminders:
        await callback.message.edit_text("📭 У вас нет активных напоминаний", reply_markup=add_new_menu_kb())
        await callback.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for r in reminders:
        title = r.title
        if len(title) > 20:
            title = title[:20] + "..."
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"{title} ({r.time_to_send})", callback_data=f"select_{r.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    await callback.message.edit_text("👀 Ваши активные напоминания:", reply_markup=kb)
    await callback.answer()
    
async def select_reminder(callback: CallbackQuery):
    rem_id = int(callback.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        reminder = await session.get(Reminder, rem_id)
    if not reminder or reminder.user_id != callback.from_user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    info = (f"📌 <b>{reminder.title}</b>\n\n"
            f"{reminder.text}\n\n"
            f"🔄 Тип: {reminder.recurrence_type}\n"
            f"⏰ Время: {reminder.time_to_send}\n"
            f"🚚 Доставка: {reminder.delivery_method}")
    if reminder.contact:
        info += f" ({reminder.contact})"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔁 Изменить название", callback_data=f"edit_title_{rem_id}")],
                                            [InlineKeyboardButton(text="✏️ Изменить текст", callback_data=f"edit_text_{rem_id}")],
                                            [InlineKeyboardButton(text="⚙️ Пересоздать", callback_data=f"recreate_{rem_id}")],
                                            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{rem_id}")],
                                            [InlineKeyboardButton(text="⬅️ Назад", callback_data="view_active")],])
    try:
        await callback.message.edit_text(info, reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

async def edit_title_start(callback: CallbackQuery, state: FSMContext):
    rem_id = int(callback.data.split("_")[2])
    await state.set_data({"mode": "edit", "rem_id": rem_id, "edit_field": "title"})
    await callback.message.edit_text("Введите новое название:")
    await state.set_state(States.title)
    await callback.answer()

async def edit_text_start(callback: CallbackQuery, state: FSMContext):
    rem_id = int(callback.data.split("_")[2])
    await state.set_data({"mode": "edit", "rem_id": rem_id, "edit_field": "text"})
    await callback.message.edit_text("Введите новый текст:")
    await state.set_state(States.text)
    await callback.answer()

async def recreate_reminder(callback: CallbackQuery, state: FSMContext):
    rem_id = int(callback.data.split("_")[1])

    async with AsyncSessionLocal() as session:
        await session.execute(delete(Reminder).where(Reminder.id == rem_id))
        await session.commit()
    try:
        from app.reminders import scheduler
        scheduler.remove_job(str(rem_id))
    except Exception:
        pass
    await callback.message.edit_text("👌🏻Старое напоминание успешно удалено. Создадим новое!")
    await add_new(callback, state)
    await callback.answer()

async def delete_reminder(callback: CallbackQuery):
    rem_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Reminder).where(
                Reminder.id == rem_id,
                Reminder.user_id == user_id
            )
        )
        await session.commit()

    try:
        from app.reminders import scheduler
        scheduler.remove_job(str(rem_id))
    except Exception:
        pass

    await callback.message.edit_text("🗑Напоминание удалено", reply_markup=main_menu_kb())
    await callback.answer()

async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отменено", reply_markup=main_menu_kb())
    await callback.answer()

def register_callback_handlers(dp: Dispatcher):
    dp.callback_query.register(cb_main_menu, F.data == "main_menu")
    dp.callback_query.register(add_new, F.data == "add_new")
    dp.callback_query.register(process_rec_type, States.recurrence_type, F.data.startswith("rec_"))
    dp.callback_query.register(process_delivery, States.delivery_method, F.data.startswith("del_"))
    dp.callback_query.register(view_active, F.data == "view_active")
    dp.callback_query.register(select_reminder, F.data.startswith("select_"))
    dp.callback_query.register(edit_title_start, F.data.startswith("edit_title_"))
    dp.callback_query.register(edit_text_start, F.data.startswith("edit_text_"))
    dp.callback_query.register(recreate_reminder, F.data.startswith("recreate_"))
    dp.callback_query.register(delete_reminder, F.data.startswith("delete_"))
    dp.callback_query.register(cancel, F.data == "cancel")
    dp.callback_query.register(help, F.data == "help")
    dp.callback_query.register(quick_title, States.title, F.data.startswith("name_"))
