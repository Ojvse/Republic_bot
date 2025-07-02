from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def location_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Добавить локацию"), KeyboardButton(text="✏️ Редактировать локацию")],
            [KeyboardButton(text="🗑 Удалить локацию"), KeyboardButton(text="📄 Список локаций")],
            [KeyboardButton(text="⬅️ Назад в админ-панель")]
        ],
        resize_keyboard=True
    )
