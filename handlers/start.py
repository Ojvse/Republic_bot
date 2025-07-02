from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from config import ADMIN_IDS
from database.models import User
from database.db import session
from keyboards.main_menu import main_menu_keyboard

router = Router()

@router.message(CommandStart())  # Обработчик команды /start
async def cmd_start(message: types.Message):
    user_id = message.from_user.id  # Получаем ID пользователя из Telegram

    # Проверяем, есть ли пользователь в базе данных
    user = session.query(User).filter_by(game_id=user_id).first()
    if not user:
        # Если пользователя нет — сообщаем об этом и завершаем выполнение
        await safe_answer(message,
            "❌ Вы не зарегистрированы.\n"
            "Обратитесь к администратору для получения доступа."
        )
        return

    # Проверяем, является ли пользователь администратором
    is_admin = user_id in ADMIN_IDS or user.is_admin

    # Отправляем приветственное сообщение и главное меню
    await safe_answer(message,
        "👋 Добро пожаловать! Выберите действие:",
        reply_markup=main_menu_keyboard(is_admin=is_admin)  # Передаём статус админа для отображения правильной клавиатуры
    )


@router.message(F.new_chat_members)  # Обработчик события добавления новых участников в чат
async def welcome_by_message(message: types.Message):
    for member in message.new_chat_members:  # Проходим по всем новым участникам
        if member.is_bot:
            continue  # Пропускаем ботов

        # Формируем текст приветственного сообщения
        welcome_text = (
            f"👋 <b>Приветствуем тебя, {member.full_name}, в ⚛️ Республике!</b>\n\n"
            "📚 /guide — гайды\n"
            "ℹ️ /info — профиль\n"
            "⚔️ /raid — рейды\n"
            "💬 Просто будь с нами!\n"
        )

        try:
            # Отправляем приветствие
            await safe_answer(message, welcome_text, parse_mode="HTML")
            print(f"[DEBUG] Приветствие отправлено в чат {message.chat.id} для {member.full_name}")
        except Exception as e:
            # Логируем ошибку, если отправка провалилась
            print(f"[ERROR] Ошибка отправки приветствия: {e}")
