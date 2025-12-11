from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏠Главное меню")],
                                        [KeyboardButton(text="💭О боте"), KeyboardButton(text="🫂Помощь")],],resize_keyboard=True,)

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📍Добавить новое", callback_data="add_new")],
                                                [InlineKeyboardButton(text="👀Посмотреть активные", callback_data="view_active")],])

def add_new_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📍Добавить новое", callback_data="add_new")],])

def add_name() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💊Таблетки", callback_data="name_med")],
                                                [InlineKeyboardButton(text="💦Вода", callback_data="name_aqua")],
                                                [InlineKeyboardButton(text="💤Сон", callback_data="name_zzz")],])

def recurrence_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="1️⃣ Один раз", callback_data="rec_once")],
                                                [InlineKeyboardButton(text="🔁 Ежедневно", callback_data="rec_daily")],
                                                [InlineKeyboardButton(text="🗓 Еженедельно", callback_data="rec_weekly")],
                                                [InlineKeyboardButton(text="📆 Ежемесячно", callback_data="rec_monthly")],
                                                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],])

def delivery_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔵 Telegram", callback_data="del_telegram")],
                                                [InlineKeyboardButton(text="🟢 WhatsApp", callback_data="del_whatsapp")],
                                                [InlineKeyboardButton(text="🟠 SMS", callback_data="del_sms")],
                                                [InlineKeyboardButton(text="📞Звонок", callback_data="del_call")],
                                                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],])

def help_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Нашли баг?", callback_data="help")],
                                                [InlineKeyboardButton(text="Напоминания не работают?", callback_data="help")],
                                                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],])

def help_kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️Назад", callback_data="main_menu")],])
