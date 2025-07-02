from aiogram.filters import StateFilter
from states.report_states import ReportBuilder
from utils.safe_send import safe_answer
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import func
from database.db import session
from database.models import User, RaidEvent, RaidParticipation, RaidPinSendLog
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from keyboards.cancel import cancel_keyboard
from services.navigation import return_to_raid_menu

router = Router()


@router.message(F.text == "📊 Отчёт по участию")
async def participation_report(message: Message):
    now = datetime.utcnow()  # Текущее время
    week_ago = now - timedelta(days=7)  # Время неделю назад

    # Запрос: Получаем пользователей и количество их участий за последние 7 дней
    report = (
        session.query(User.nickname, func.count(RaidParticipation.id))
        .join(RaidParticipation, User.id == RaidParticipation.user_id)
        .join(RaidEvent, RaidEvent.id == RaidParticipation.raid_id)
        .filter(RaidEvent.start_time >= week_ago)  # Только рейды за последние 7 дней
        .group_by(User.nickname)  # Группируем по пользователям
        .order_by(func.count(RaidParticipation.id).desc())  # Сортируем по количеству участий (убывание)
        .all()
    )

    if not report:
        await safe_answer(message, "Нет данных за неделю.")
        await return_to_raid_menu(message)  # Возвращаемся в меню
        return

    # Формируем текст отчёта
    lines = [f"{i+1}. <b>{nick}</b> — {count}" for i, (nick, count) in enumerate(report)]
    await safe_answer(
        message,
        "<b>📊 Активность за 7 дней:</b>\n" + "\n".join(lines),
        parse_mode="HTML"
    )
    await return_to_raid_menu(message)  # Возвращаемся в меню


@router.message(F.text == "👥 Участники рейда")
async def raid_participant_report(message: Message, state: FSMContext):
    # Получаем последние 10 рейдов из БД
    raids = (
        session.query(RaidEvent)
        .order_by(RaidEvent.start_time.desc())
        .limit(10)
        .all()
    )

    if not raids:
        await safe_answer(message, "📭 Нет рейдов.")
        await return_to_raid_menu(message)
        return

    # Формируем список ID рейдов
    raid_ids = [r.id for r in raids]
    # Формируем текст с описанием каждого рейда
    lines = [
        f"{i+1}. Рейд #{r.id} — {r.name}\n"
        f"    🕓 {r.start_time.strftime('%d.%m %H:%M')}"
        for i, r in enumerate(raids)
    ]

    # Сохраняем список ID для дальнейшего использования
    await state.update_data(raid_list=raid_ids)

    # Запрашиваем у пользователя номер рейда
    await safe_answer(
        message,
        "📋 <b>Выберите рейд для отчёта, введя его номер:</b>\n\n" + "\n\n".join(lines),
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ReportBuilder.filter_value)  # Устанавливаем состояние ожидания ввода


@router.message(StateFilter(ReportBuilder.filter_value), F.text.regexp(r"^\d+$").as_("match"))
async def raid_number_choice(message: Message, state: FSMContext, match):
    data = await state.get_data()
    raid_list = data.get("raid_list")  # Получаем список ID рейдов
    if not raid_list:
        await safe_answer(message, "⚠️ Нет активного выбора рейда.")
        await return_to_raid_menu(message)
        return

    idx = int(message.text.strip()) - 1  # Получаем индекс выбранного рейда
    if idx < 0 or idx >= len(raid_list):
        await safe_answer(message, "❌ Неверный номер рейда.")
        return

    raid_id = raid_list[idx]  # Получаем ID выбранного рейда
    raid = session.query(RaidEvent).filter_by(id=raid_id).first()
    if not raid:
        await safe_answer(message, "❌ Рейд не найден.")
        await return_to_raid_menu(message)
        return

    # Получаем участников этого рейда
    parts = (
        session.query(User.nickname, User.id, RaidParticipation.status, RaidParticipation.joined_at)
        .join(User, User.id == RaidParticipation.user_id)
        .filter(RaidParticipation.raid_id == raid_id)
        .all()
    )

    # Разделяем участников по статусам
    signed = [(n, t) for n, uid, s, t in parts if s == "записался"]
    refused = [(n, t) for n, uid, s, t in parts if s == "отказался"]
    signed_ids = [uid for _, uid, s, _ in parts if s == "записался"]
    refused_ids = [uid for _, uid, s, _ in parts if s == "отказался"]

    # Получаем список всех приглашённых
    invited_ids = [
        r.target_id for r in session.query(RaidPinSendLog.target_id)
        .filter_by(raid_id=raid_id)
        .distinct()
        .all()
    ]

    # Вычисляем тех, кто не подтвердил участие
    not_responded_ids = set(invited_ids) - set(signed_ids) - set(refused_ids)
    not_responded = session.query(User.nickname).filter(User.id.in_(not_responded_ids)).all()

    # Вспомогательные функции для форматирования списков
    def format_list(users):
        return "\n".join(f"• {n} ({t.strftime('%d.%m %H:%M')})" for n, t in users) if users else "—"

    def format_simple(users):
        return "\n".join(f"• {n.nickname}" for n in users) if users else "—"

    # Формируем итоговый текст отчёта
    await safe_answer(
        message,
        f"📋 <b>Участники рейда: {raid.name}</b>\n\n"
        f"👥 Приглашено: {len(invited_ids)}\n\n"
        f"⚔ Записались ({len(signed)}):\n{format_list(signed)}\n\n"
        f"🚫 Отказались ({len(refused)}):\n{format_list(refused)}\n\n"
        f"❔ Не подтвердили ({len(not_responded)}):\n{format_simple(not_responded)}",
        parse_mode="HTML"
    )
    await return_to_raid_menu(message)  # Возвращаемся в меню


@router.message(F.text == "Отмена")
async def cancel_raid_selection(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние
    await return_to_raid_menu(message)  # Возвращаемся в меню
