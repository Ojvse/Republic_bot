from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def raid_main_menu(is_admin=False):
    buttons = [
        [KeyboardButton(text="📅 Предстоящие рейды"), KeyboardButton(text="📊 Моя активность")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    if is_admin:
        buttons.insert(1, [KeyboardButton(text="🛠 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def raid_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            # 📂 Рейды + Пины
            [KeyboardButton(text="➕ Новый рейд"), KeyboardButton(text="📋 Список рейдов")],
            [KeyboardButton(text="📍 Выдать пин для рейда"), KeyboardButton(text="👥 Участники рейда")],
            [KeyboardButton(text="📒 Журнал пинов"), KeyboardButton(text="🗑 Удалить рейд")],

            # 📂 Прочее
            [KeyboardButton(text="⬅️ Назад в админ-панель")]
        ],
        resize_keyboard=True
    )
