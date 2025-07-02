from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database.db import session
from database.models import User, RaidEvent, RaidParticipation, RaidReminder, RaidPinData
from utils.safe_send import safe_answer

router = Router()


# Функция для построения клавиатуры рейда (кнопки "Записаться", "Отменить", "Напомнить")
def build_raid_markup(raid_id: int, user_participates: bool) -> InlineKeyboardMarkup:
    first_row = []
    if user_participates:
        # Если пользователь записан — кнопка "Вы записаны" и "Я не иду"
        first_row.append(
            InlineKeyboardButton(text=f"⚔ Вы записаны", callback_data=f"raid_join_{raid_id}")
        )
        first_row.append(
            InlineKeyboardButton(text=f"🚫 Я не иду", callback_data=f"raid_leave_{raid_id}")
        )
    else:
        # Если не записан — кнопка "Я иду!" и "Отменить"
        first_row.append(
            InlineKeyboardButton(text=f"⚔ Я иду!", callback_data=f"raid_join_{raid_id}")
        )
        first_row.append(
            InlineKeyboardButton(text=f"🚫 Отменить", callback_data=f"raid_leave_{raid_id}")
        )
    second_row = [
        InlineKeyboardButton(text=f"🔔 Напомнить", callback_data=f"remind_{raid_id}")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[first_row, second_row])


# Обработчик для отображения ближайших активных рейдов
@router.callback_query(F.data == "raid_upcoming")
async def raid_upcoming_handler(callback: CallbackQuery):
    await callback.answer()  # Подтверждение получения запроса
    now = datetime.utcnow()  # Текущее время (UTC)

    # Получаем до 5 активных будущих рейдов
    events = (
        session.query(RaidEvent)
        .filter(RaidEvent.start_time >= now, RaidEvent.status == "active")  # Только будущие и активные
        .order_by(RaidEvent.start_time.asc())  # Сортируем по времени (сначала ближайшие)
        .limit(5)  # Ограничиваем до 5
        .all()
    )

    if not events:
        # Если рейдов нет — сообщаем об этом
        await safe_answer(callback.message, "❌ Нет запланированных рейдов.")
        return

    # Получаем пользователя из БД
    user = session.query(User).filter_by(game_id=callback.from_user.id).first()

    for ev in events:
        dt = ev.start_time.strftime("%d.%m %H:%M")  # Форматируем дату старта
        # Словарь для иконок статуса
        icon = {"active": "⏳", "finished": "✅", "cancelled": "❌"}
        text = (
            f"{icon.get(ev.status, '❓')} <b>Рейд:</b> {ev.name}\n"
            f"🕔 <b>Время:</b> {dt}\n"
            f"🎯 <b>Банда:</b> {ev.squad}"
        )

        participates = False
        if user:
            # Проверяем, записан ли пользователь на этот рейд
            participates = (
                session.query(RaidParticipation)
                .filter_by(raid_id=ev.id, user_id=user.id)
                .first()
                is not None
            )

        # Отправляем сообщение с рейдом и кнопками
        await safe_answer(
            callback.message,
            text,
            parse_mode="HTML",
            reply_markup=build_raid_markup(ev.id, participates),
        )


# Обработчик для записи на рейд
@router.callback_query(F.data.startswith("raid_join_"))
async def raid_join_handler(callback: CallbackQuery):
    _, _, sid = callback.data.split("_")
    raid_id = int(sid)  # Извлекаем ID рейда

    # Получаем пользователя и рейд
    user = session.query(User).filter_by(game_id=callback.from_user.id).first()
    raid = session.query(RaidEvent).filter_by(id=raid_id).first()
    if not user or not raid:
        await callback.answer("❌ Пользователь или рейд не найдены.", show_alert=True)
        return

    now = datetime.utcnow()

    # Проверяем участие пользователя в этом рейде
    part = session.query(RaidParticipation).filter_by(raid_id=raid_id, user_id=user.id).first()
    if part:
        part.status = "записался"
        part.joined_at = now
    else:
        # Добавляем новую запись участия
        session.add(RaidParticipation(
            raid_id=raid_id,
            user_id=user.id,
            status="записался",
            joined_at=now,
        ))
    session.commit()

    # Получаем данные пина
    pin_data = session.query(RaidPinData).filter_by(raid_id=raid.id).first()

    title = pin_data.title if pin_data else raid.name
    km = pin_data.km if pin_data else "Не указан"
    description = pin_data.description if pin_data else ""

    dt = raid.start_time.strftime("%d.%m %H:%M")
    text = (
        f"⏳ <b>Рейд:</b> {raid.name}\n"
        f"<b>{title}</b>\n"
        f"Точка сбора:📍 {km} км\n"
        f"{description}\n"
        f"🕔 <b>Время:</b> {dt}\n"
        f"🎯 <b>Банда:</b> {raid.squad or 'Нет'}\n"
        f"📌 <b>Ваш статус:</b> ⚔ Записался"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚔ Вы записаны", callback_data=f"raid_join_{raid.id}"),
            InlineKeyboardButton(text="🚫 Я не иду", callback_data=f"raid_leave_{raid.id}")
        ],
        [
            InlineKeyboardButton(text="🔔 Напомнить", callback_data=f"remind_{raid.id}")
        ]
    ])

    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer("✅ Вы успешно записались на рейд!")


# Обработчик установки напоминания о рейде
@router.callback_query(F.data.startswith("remind_"))
async def remind_user(callback: CallbackQuery):
    _, sid = callback.data.split("_")
    raid_id = int(sid)  # Извлекаем ID рейда

    # Получаем пользователя
    user = session.query(User).filter_by(game_id=callback.from_user.id).first()
    if not user:
        await callback.answer("⚠️ Пользователь не найден.", show_alert=True)
        return

    # Проверяем, установлено ли уже напоминание
    exists = (
        session.query(RaidReminder)
        .filter_by(raid_id=raid_id, user_id=user.id)
        .first()
    )
    if exists:
        await callback.answer("🔔 Напоминание уже установлено!")
        return

    # Создаём новое напоминание
    session.add(RaidReminder(raid_id=raid_id, user_id=user.id))
    session.commit()
    await callback.answer("✅ Напомним за час до рейда.")
