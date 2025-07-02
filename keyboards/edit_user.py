from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def skip_or_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
