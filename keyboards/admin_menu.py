
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def full_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Рейды"), KeyboardButton(text="📘 Гайды (разделы)")],
            [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="📍 Локации"), KeyboardButton(text="❓ Справка")],
            [KeyboardButton(text="⬅️ Выйти в главное меню")]
        ],
        resize_keyboard=True
    )


def user_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/add_user"), KeyboardButton(text="/add_user_forward")],
            [KeyboardButton(text="/edit_user <ID>"), KeyboardButton(text="/remove_user <ID>")],
            [KeyboardButton(text="/list_users"), KeyboardButton(text="/access")],
            [KeyboardButton(text="⬅️ Назад в админ-панель")]
        ],
        resize_keyboard=True
    )


def guidepage_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить гайд"), KeyboardButton(text="✏️ Редактировать гайд")],
            [KeyboardButton(text="🗑 Удалить гайд"), KeyboardButton(text="📄 Список гайдов")],
            [KeyboardButton(text="⬅️ Назад в админ-панель")]
        ],
        resize_keyboard=True
    )
