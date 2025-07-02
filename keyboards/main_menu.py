from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard(is_admin: bool = False):
    keyboard = [
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="🔄 Обновить данные")],
        [KeyboardButton(text="🎓 Академия"), KeyboardButton(text="📚 Гайды")],
    ]

    # если админ — рейды + админка в одну строку
    if is_admin:
        keyboard.append([
            KeyboardButton(text="⚔️ Рейды"),
            KeyboardButton(text="🛠 Админ панель")
        ])
    else:
        keyboard.append([
            KeyboardButton(text="⚔️ Рейды")
        ])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
