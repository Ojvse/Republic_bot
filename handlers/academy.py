from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(F.text == "🎓 Академия")
async def academy_menu(message: Message, state: FSMContext):
    # Очищаем текущее состояние пользователя (если оно было активно)
    await state.clear()

    # Отправляем пользователю сообщение с приветствием и информацией о разделе "Академия"
    # Используем функцию safe_answer для безопасной отправки сообщения
    await safe_answer(
        message,
        "🏛 <b>Академия Республики</b>\n\n"
        "Здесь вы можете изучить различные аспекты игры:\n\n"
        "https://t.me/+A-PDIXjcCz0xZTAy",
        parse_mode="HTML"  # Включаем поддержку HTML-разметки для жирного текста
    )
