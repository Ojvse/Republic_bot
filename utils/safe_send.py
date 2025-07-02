from aiogram.enums import ChatType
from aiogram.types import Message
from aiogram import Bot


async def safe_answer(message: Message, text: str, reply_markup=None, **kwargs):
    # Проверяем, является ли чат приватным. Если нет, убираем клавиатуру
    if message.chat.type != ChatType.PRIVATE:
        reply_markup = None
    # Отправляем ответное сообщение с текстом и, при необходимости, клавиатурой
    return await message.answer(text, reply_markup=reply_markup, **kwargs)


async def safe_send_message(bot: Bot, chat_id: int, text: str, reply_markup=None, **kwargs):
    # Получаем информацию о чате по его ID
    chat = await bot.get_chat(chat_id)
    # Если чат не является приватным, убираем клавиатуру
    if chat.type != ChatType.PRIVATE:
        reply_markup = None
    # Отправляем сообщение в указанный чат
    return await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, **kwargs)
