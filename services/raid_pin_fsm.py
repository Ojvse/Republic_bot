from utils.safe_send import safe_answer, safe_send_message

from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from states.raid_states import RaidAlert
from database.models import User
from database.db import session
from keyboards.cancel import cancel_keyboard

# Начало процесса создания ПИН-сообщения (начальное состояние)
async def start_pin_fsm(message: Message, state: FSMContext, from_menu: str = "raid_admin"):
    await state.clear()
    await state.update_data(from_menu=from_menu)
    await safe_answer(message, "🕔 Введите время рейда (например, 17:00):", reply_markup=cancel_keyboard())
    await state.set_state(RaidAlert.time)


# Обработка шагов ввода данных для ПИН-сообщения
async def process_pin_step(state: FSMContext, step: str, message: Message) -> bool:
    # Проверка на отмену действия
    if (message.text or "").lower() == "отмена":
        await state.clear()
        from keyboards.raid_menu import raid_admin_menu
        await safe_answer(message, "❌ Действие отменено.", reply_markup=raid_admin_menu())
        return False

    # Шаг 1: Введено время, запрашиваем место сбора
    if step == "time":
        await state.update_data(time=message.text)
        await safe_answer(message, "📌 Укажите место сбора (например, 5 км):")
        await state.set_state(RaidAlert.location)

    # Шаг 2: Введено место, запрашиваем дополнительный текст
    elif step == "location":
        await state.update_data(location=message.text)
        await safe_answer(message, "📝 Введите дополнительный текст (или '-' чтобы пропустить):")
        await state.set_state(RaidAlert.pin_value)

    # Шаг 3: Введен дополнительный текст, формируем клавиатуру с выбором банды или "Отправить всем"
    elif step == "pin_value":
        dop_text = "" if message.text.strip() == "-" else message.text.strip()
        await state.update_data(dop_text=dop_text)

        # Получаем уникальные названия отрядов из базы данных
        squads = session.query(User.squad).distinct().all()
        buttons = [[KeyboardButton(text=s[0])] for s in squads if s[0]]
        buttons.append([KeyboardButton(text="Отправить всем")])
        keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

        await safe_answer(message, "🎯 Кому отправить ПИН?", reply_markup=keyboard)
        await state.set_state(RaidAlert.confirm)

    return True
