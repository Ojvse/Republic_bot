from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def info_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Обновить данные")],
            [KeyboardButton(text="👤 Посмотреть мой профиль")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )