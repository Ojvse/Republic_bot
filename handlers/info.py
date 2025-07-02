from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.types import Message
from database.models import User, PlayerProfile
from database.db import session
from zoneinfo import ZoneInfo
from sqlalchemy import func

router = Router()


@router.message(F.text == "/me")
async def show_own_profile(message: Message):
    # Ищем пользователя в БД по его Telegram ID
    user = session.query(User).filter_by(game_id=message.from_user.id).first()
    if not user:
        await safe_answer(message, "❌ Вы не зарегистрированы.")
        return

    try:
        # Отправляем информацию о профиле текущего пользователя
        await safe_answer(message, format_user_info(user), parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] /me: {e}")
        await safe_answer(message, "❌ Ошибка при выводе профиля.")


@router.message(F.text.regexp(r"^/info_(.+)$").as_("match"))
async def show_profile_by_direct_command(message: Message, match):
    # Извлекаем никнейм или ID из команды вида /info_никнейм или /info_ID
    query = match.group(1).strip()
    user = try_get_user_from_text(query)
    if not user:
        await safe_answer(message, "❌ Пользователь не найден.")
        return

    try:
        # Отправляем информацию о найденном пользователе
        await safe_answer(message, format_user_info(user), parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] /info_<user>: {e}")
        await safe_answer(message, "❌ Ошибка при выводе профиля.")


@router.message(lambda m: m.text and m.text.startswith("/info"))
async def show_other_profile(message: Message):
    text = message.text.strip()
    parts = text.split(maxsplit=1)

    # Извлекаем команду и аргумент (если есть)
    command = parts[0].split("@")[0]
    arg = parts[1].strip() if len(parts) > 1 else None

    target_id = None

    # Если сообщение является ответом — определяем ID целевого пользователя
    if message.reply_to_message:
        if message.reply_to_message.forward_from:
            target_id = message.reply_to_message.forward_from.id
        else:
            target_id = message.reply_to_message.from_user.id

    elif arg:
        # Если указан аргумент — ищем пользователя по нему
        user = try_get_user_from_text(arg)
        if not user:
            await safe_answer(message, "❌ Пользователь не найден.")
            return
        await safe_answer(message, format_user_info(user), parse_mode="HTML")
        return

    # Если не было реплая и нет аргумента — показываем помощь
    if not target_id:
        await safe_answer(message,
            "ℹ️ Используйте:\n"
            "• <code>/info</code> в ответ на сообщение\n"
            "• <code>/info ID</code> или <code>/info Ник</code>\n"
            "• <code>/info_Ник</code> или <code>/info_ID</code> — напрямую",
            parse_mode="HTML"
        )
        return

    # Ищем пользователя по найденному ID
    user = session.query(User).filter_by(game_id=target_id).first()
    if not user:
        await safe_answer(message, "❌ Пользователь не найден.")
        return

    try:
        # Отправляем информацию о найденном пользователе
        await safe_answer(message, format_user_info(user), parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] /info: {e}")
        await safe_answer(message, "❌ Ошибка при выводе профиля.")


def try_get_user_from_text(text: str):
    # Пытаемся найти пользователя по тексту (ID или никнейму)
    if text.isdigit():
        return session.query(User).filter_by(game_id=int(text)).first()
    return session.query(User).filter(func.lower(User.nickname) == text.lower()).first()


def format_user_info(user: User) -> str:
    # Получаем подробный профиль пользователя
    profile = session.query(PlayerProfile).filter_by(game_id=user.game_id).first()

    # Формируем строку с базовой информацией
    faction = user.faction or (profile.faction if profile else None) or "-"
    squad = user.squad or (profile.squad if profile else None) or "-"

    base = (
        f"📟 <b>Профиль игрока</b>\n"
        f"🆔 <b>ID:</b> {user.game_id}\n"
        f"🧑 <b>Ник:</b> {user.nickname}\n"
        f"⚛️ <b>Фракция:</b> {faction}\n"
        f"🤟 <b>Банда:</b> {squad}\n"
        f"🎭 <b>Роль:</b> {user.role or '-'}\n"
        f"📅 <b>Дата добавления:</b> {user.created_at.replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')}\n"
    )

    if not profile:
        return base + "\nℹ️ Подробный профиль ещё не загружен."

    detailed = (
        #f"\n❤️ <b>Здоровье:</b> {profile.health_current}/{profile.health_max}\n"
        f"\n❤️ <b>Здоровье:</b> {profile.health_max}\n"
        f"⚔️ <b>Урон:</b> {profile.damage or 0} | 🛡 <b>Броня:</b> {profile.armor or 0}\n"
        f"💪 Сила: {profile.strength or 0} | 🎯 Меткость: {profile.accuracy or 0}\n"
        f"🗣 Харизма: {profile.charisma or 0} | 🤸🏽‍♂️ Ловкость: {profile.agility or 0}\n"
        #f"🔋 Выносливость: {profile.stamina_current}/{profile.stamina_max}\n"
        f"🔋 Выносливость: {profile.stamina_max}\n"
        f"📍 Локация: {profile.location or '-'} ({profile.distance_km or 0} км)\n"
        f"\n📅 Обновлено: {profile.updated_at.replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')}"
    )

    return base + detailed
