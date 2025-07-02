from utils.safe_send import safe_answer
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import func
from database.db import session
from database.models import RaidPinSendLog, User

router = Router()


@router.message(F.text == "📒 Журнал пинов")
async def view_pin_send_log(message: Message):
    # Выполняем группировку записей из таблицы RaidPinSendLog:
    # - Группируем по админу и тексту пина
    # - Для каждой группы получаем минимальную дату отправки (время первой отправки)
    # - Считаем количество получателей
    # - Сортируем по времени в обратном порядке (сначала самые новые)
    # - Ограничиваем результат 10 записями
    grouped_logs = (
        session.query(
            RaidPinSendLog.admin_id,
            RaidPinSendLog.pin_text,
            func.min(RaidPinSendLog.sent_at).label("sent_at"),
            func.count(RaidPinSendLog.target_id).label("recipients_count")
        )
        .group_by(RaidPinSendLog.admin_id, RaidPinSendLog.pin_text)
        .order_by(func.min(RaidPinSendLog.sent_at).desc())
        .limit(10)
        .all()
    )

    if not grouped_logs:
        # Если журнал пуст — сообщаем об этом
        await safe_answer(message, "📭 Журнал пуст.")
        return

    # Начинаем формировать ответ: заголовок и легенду
    lines = [
        "📒 <b>Последние 10 отправленных пинов:</b>\n"
        "ℹ️ <b>Обозначения:</b>\n"
        "🛡 — Отправитель пина (админ)\n"
        "🕓 — Время отправки\n"
        "👥 — Количество получателей\n"
        "📩 — Заголовок пина\n"
        "📍 — Локация\n"
        ""
    ]

    # Проходимся по каждой записи из результата запроса
    for i, log in enumerate(grouped_logs, start=1):
        # Получаем администратора по его ID
        admin = session.query(User).filter_by(game_id=log.admin_id).first()
        admin_name = admin.nickname if admin else f"id:{log.admin_id}"

        # Форматируем дату отправки
        time = log.sent_at.strftime('%d.%m %H:%M')

        # Разбиваем текст пина на строки и очищаем от лишних пробелов
        pin_lines = [line.strip() for line in log.pin_text.splitlines() if line.strip()]
        title = pin_lines[0] if len(pin_lines) > 0 else "-"  # Заголовок
        location = pin_lines[1] if len(pin_lines) > 1 else "-"  # Локация
        body = " ".join(pin_lines[2:]) if len(pin_lines) > 2 else "-"  # Основной текст
        if len(body) > 150:
            body = body[:147] + "..."  # Обрезаем длинный текст

        # Формируем строку с информацией о пине
        lines.append(
            f"{i}. 🛡 <b>{admin_name}</b> | 🕓 {time} | 👥 {log.recipients_count}\n"
            f"    📩 <b>{title}</b>\n"
            f"    {location}\n"
            f"    {body}"
        )

    # Склеиваем все строки в одно сообщение
    text = "\n\n".join(lines)
    # Отправляем пользователю сформированный текст
    await safe_answer(message, text, parse_mode="HTML")
