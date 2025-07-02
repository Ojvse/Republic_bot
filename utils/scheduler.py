from utils.safe_send import safe_send_message
import asyncio
from datetime import datetime, timedelta
from pytz import timezone
from database.db import session
from database.models import RaidEvent, RaidParticipation, User, RaidReminder

# Установка часового пояса — Москва
moscow = timezone("Europe/Moscow")


async def raid_reminder_loop(bot):
    # Бесконечный цикл для проверки рейдов и отправки напоминаний
    while True:
        # Получаем текущее время в часовом поясе Москвы
        now = datetime.now(moscow)

        # 1. Завершить рейды, которые начались более чем 2 часа назад
        expired_raids = (
            session.query(RaidEvent)
            .filter(
                RaidEvent.start_time < now - timedelta(hours=2),
                RaidEvent.status == "active"
            )
            .all()
        )
        for raid in expired_raids:
            raid.status = "finished"
        session.commit()

        # 2. Обновить статус участников, которые записались на завершенные рейды
        participations = (
            session.query(RaidParticipation)
            .join(RaidEvent)
            .filter(
                RaidEvent.status == "finished",
                RaidParticipation.status == "записался"
            )
            .all()
        )
        for part in participations:
            part.status = "участвовал"
        session.commit()

        # 3. Напоминание за 30 минут до старта (окно: 29-31 минут до события)
        window_start = now + timedelta(minutes=29)
        window_end = now + timedelta(minutes=31)

        # Находим активные рейды, которые начнутся в этом окне
        upcoming_raids = (
            session.query(RaidEvent)
            .filter(
                RaidEvent.start_time.between(window_start, window_end),
                RaidEvent.status == "active"
            )
            .all()
        )

        # Отправляем напоминания всем участникам этих рейдов
        for event in upcoming_raids:
            participants = (
                session.query(User)
                .join(RaidParticipation, RaidParticipation.user_id == User.id)
                .filter(
                    RaidParticipation.raid_id == event.id,
                    RaidParticipation.status == "записался"
                )
                .all()
            )

            for user in participants:
                if user.game_id:
                    dt_str = event.start_time.strftime('%d.%m %H:%M')
                    try:
                        await safe_send_message(
                            bot,
                            chat_id=user.game_id,
                            text=(
                                f"⏰ <b>Напоминание о рейде!</b>\n\n"
                                f"⚔ Рейд: {event.name}\n"
                                f"🕔 Время: {dt_str}\n"
                                f"📍 Не забудьте вовремя прийти!"
                            ),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"[ERROR] Не удалось отправить сообщение пользователю {user.id}: {e}")

        # 4. Напомнить за 1 час до старта (окно: 59-61 минут до события)
        remind_window_start = now + timedelta(minutes=59)
        remind_window_end = now + timedelta(minutes=61)

        # Находим активные рейды, которые начнутся в этом окне
        events_to_remind = (
            session.query(RaidEvent)
            .filter(
                RaidEvent.start_time.between(remind_window_start, remind_window_end),
                RaidEvent.status == "active"
            )
            .all()
        )

        # Отправляем напоминания всем пользователям, установившим напоминание
        for event in events_to_remind:
            reminders = session.query(RaidReminder).filter_by(raid_id=event.id).all()
            for r in reminders:
                user = session.query(User).filter_by(id=r.user_id).first()
                if user and user.game_id:
                    try:
                        await safe_send_message(
                            bot,
                            chat_id=user.game_id,
                            text=f"🔔 Напоминание: рейд '{event.name}' начнётся через 1 час!",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"[ERROR] Не удалось отправить напоминание пользователю {user.id}: {e}")

            # После отправки удаляем все напоминания для этого рейда
            session.query(RaidReminder).filter_by(raid_id=event.id).delete()
            session.commit()

        # Пауза на 60 секунд перед следующей итерацией цикла
        await asyncio.sleep(60)
