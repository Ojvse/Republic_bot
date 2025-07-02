from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

delete_confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[[
        KeyboardButton(text="✅ Подтвердить удаление"),
        KeyboardButton(text="❌ Отмена удаления")
    ]],
    resize_keyboard=True,
    one_time_keyboard=True
)
