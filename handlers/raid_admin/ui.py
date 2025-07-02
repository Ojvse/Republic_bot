from datetime import datetime, timedelta

from sqlalchemy import func

from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from services.navigation import return_to_main_menu
from keyboards.admin_menu import full_admin_menu
from database.db import session
from database.models import RaidEvent, RaidParticipation, User, RaidPinData

router = Router()

@router.message(F.text == "⚔️ Рейды")
async def open_raid_menu(message: Message):
    # Открываем главное меню рейдов для пользователя
    # Выводим текст приветствия и клавиатуру с кнопками
    await safe_answer(message,
        "📅 Меню рейдов:\n\nВы можете посмотреть ближайшие рейды и свою активность за последние 7 дней.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Предстоящие рейды"), KeyboardButton(text="📊 Моя активность")],
                [KeyboardButton(text="⬅️ Назад")]
            ],
            resize_keyboard=True
        )
    )


@router.message(F.text == "⬅️ Назад в админ-панель")
async def back_to_admin_from_raid(message: Message):
    # Обработчик кнопки "Назад" — возвращаем пользователя обратно в админ-меню
    await safe_answer(message, "↩️ Назад в админ-панель", reply_markup=full_admin_menu())


@router.message(F.text == "⬅️ Назад")
async def back_from_anywhere(message: Message):
    # Общая обработка кнопки "Назад" — возвращаем в главное меню
    await return_to_main_menu(message)


@router.message(F.text == "📋 Список рейдов")
async def list_recent_raids(message: Message):
    # Получаем последние 10 рейдов из БД, отсортированных по дате (сначала новые)
    raids = (
        session.query(RaidEvent)
        .order_by(RaidEvent.start_time.desc())
        .limit(10)
        .all()
    )

    if not raids:
        # Если рейдов нет — сообщаем об этом
        await safe_answer(message, "❌ Нет рейдов.")
        return

    lines = []
    for raid in raids:
        dt = raid.start_time.strftime('%d.%m %H:%M')
        # Формируем строку с информацией о каждом рейде
        lines.append(f"• <b>{raid.name}</b> — {dt} | 👥 {raid.squad} | ID: {raid.id}")

    # Отправляем список рейдов пользователю
    await safe_answer(message, "<b>📋 Последние рейды:</b>\n\n" + "\n".join(lines), parse_mode="HTML")


@router.message(F.text == "📅 Предстоящие рейды")
async def show_upcoming_raids(message: Message):
    now = datetime.utcnow()  # Текущее время
    # Получаем до 10 активных будущих рейдов
    raids = (
        session.query(RaidEvent)
        .filter(RaidEvent.start_time >= now, RaidEvent.status == "active")  # Только будущие и активные
        .order_by(RaidEvent.start_time.asc())  # Сортируем по времени (сначала ближайшие)
        .limit(10)  # Ограничиваем до 10
        .all()
    )

    if not raids:
        # Если рейдов нет — сообщаем об этом
        await safe_answer(message, "❌ Нет запланированных рейдов.")
        return

    user = session.query(User).filter_by(game_id=message.from_user.id).first()

    for raid in raids:
        dt = raid.start_time.strftime("%d.%m %H:%M")

        # По умолчанию статус — не выбрано
        part_status = "❔ Не выбрано"
        join_text = "⚔ Я иду!"
        leave_text = "🚫 Отменить"

        # Проверяем участие пользователя
        if user:
            part = session.query(RaidParticipation).filter_by(raid_id=raid.id, user_id=user.id).first()
            if part:
                if part.status == "записался":
                    part_status = "⚔ Записался"
                    join_text = "⚔ Вы записаны"
                    leave_text = "🚫 Я не иду"
                elif part.status == "отказался":
                    part_status = "🚫 Отказался"
                    join_text = "⚔ Я иду!"
                    leave_text = "🚫 Вы отказались"

        # Получаем данные пина
        pin_data = session.query(RaidPinData).filter_by(raid_id=raid.id).first()

        title = pin_data.title if pin_data else raid.name
        km = pin_data.km if pin_data else "Не указан"
        description = pin_data.description if pin_data else ""

        # Формируем текст с информацией о рейде
        text = (
            f"⏳ <b>Рейд:</b> {raid.name}\n"
            f"<b>{title}</b>\n"
            f"Точка сбора:📍 {km} км\n"
            f"{description}\n"
            f"🕔 <b>Время:</b> {dt}\n"
            f"🎯 <b>Банда:</b> {raid.squad or 'Нет'}\n"
            f"📌 <b>Ваш статус:</b> {part_status}"
        )

        # Создаём клавиатуру с кнопками
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=join_text, callback_data=f"raid_join_{raid.id}"),
                InlineKeyboardButton(text=leave_text, callback_data=f"raid_leave_{raid.id}")
            ],
            [
                InlineKeyboardButton(text="🔔 Напомнить", callback_data=f"remind_{raid.id}")
            ]
        ])

        # Отправляем сообщение с рейдом и кнопками
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(F.text == "📊 Моя активность")
async def my_raid_stats(message: Message):
    # Получаем пользователя из БД
    user = session.query(User).filter_by(game_id=message.from_user.id).first()
    if not user:
        await safe_answer(message, "❌ Вы не зарегистрированы.")
        return

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)  # Время неделю назад

    # Считаем количество участий пользователя за последние 7 дней
    count = (
        session.query(func.count(RaidParticipation.id))
        .join(RaidEvent, RaidParticipation.raid_id == RaidEvent.id)
        .filter(RaidParticipation.user_id == user.id)
        .filter(RaidEvent.start_time >= week_ago)
        .scalar()
    )

    # Отправляем статистику
    await safe_answer(message, f"📊 Вы участвовали в <b>{count}</b> рейдах за последние 7 дней.", parse_mode="HTML")
