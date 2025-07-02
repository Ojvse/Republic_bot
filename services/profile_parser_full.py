from utils.safe_send import safe_answer
import re
from aiogram.types import Message
from datetime import datetime
from database.db import session
from database.models import PlayerProfile, User


async def parse_full_profile(message: Message, silent: bool = False, added_by_admin: bool = False):
    # Получаем текст сообщения и разбиваем его на строки
    text = message.text
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Словарь для хранения извлечённых данных профиля
    data = {}
    gear_lines = []
    in_gear_block = False  # Флаг для определения блока "Экипировка"

    # Парсим каждую строку
    for idx, line in enumerate(lines):
        # Извлекаем никнейм и фракцию
        if re.search(r",\s+⚛️", line):
            match = re.match(r"(.+),\s+⚛️(.+)", line)
            if match:
                data["nickname"], data["faction"] = match.groups()

        # Извлекаем банду (сquad)
        if "Банда:" in line:
            data["squad"] = line.split(":", 1)[-1].strip()

        # Извлекаем здоровье (текущее и максимальное)
        if "Здоровье" in line:
            nums = re.findall(r"\d+", line)
            if len(nums) == 2:
                data["health_current"], data["health_max"] = map(int, nums)

        # Извлекаем уровень голода
        if "Голод" in line:
            if match := re.search(r"(\d+)%", line):
                data["hunger"] = int(match.group(1))

        # Урон
        if "⚔️Урон" in line:
            if match := re.search(r"⚔️Урон: (\d+)", line):
                data["damage"] = int(match.group(1))

        # Броня
        if "🛡Броня" in line:
            if match := re.search(r"🛡Броня: (\d+)", line):
                data["armor"] = int(match.group(1))

        # Характеристики: Сила, Меткость, Харизма, Ловкость
        if "Сила:" in line or "Меткость:" in line or "Харизма:" in line or "Ловкость:" in line:
            if match := re.search(r"💪Сила: (\d+)", line):
                data["strength"] = int(match.group(1))
            if match := re.search(r"🎯Меткость: (\d+)", line):
                data["accuracy"] = int(match.group(1))
            if match := re.search(r"🗣Харизма: (\d+)", line):
                data["charisma"] = int(match.group(1))
            if match := re.search(r"🤸🏽‍♂️Ловкость: (\d+)", line):
                data["agility"] = int(match.group(1))

        # Выносливость
        if "Выносливость" in line:
            nums = re.findall(r"\d+", line)
            if len(nums) == 2:
                data["stamina_current"], data["stamina_max"] = map(int, nums)

        # Локация и расстояние
        if "📍" in line:
            if match := re.search(r"📍(.+?),", line):
                data["location"] = match.group(1).strip()
            if match := re.search(r"(\d+)км", line):
                data["distance_km"] = int(match.group(1))

        # Начало блока "Экипировка"
        if line.startswith("Экипировка"):
            in_gear_block = True
            continue
        if in_gear_block:
            if any(line.startswith(x) for x in ("Ресурсы", "Репутация", "ID", "Рейд в")):
                in_gear_block = False
            else:
                gear_lines.append(line)

        # Крышки
        if "Крышки" in line:
            if match := re.search(r"Крышки:\s*(\d+)", line):
                data["caps"] = int(match.group(1))

        # Материалы
        if "Материалы" in line:
            if match := re.search(r"Материалы:\s*(\d+)", line):
                data["materials"] = int(match.group(1))

        # Пупсы
        if "Пупсы" in line:
            if match := re.search(r"Пупсы:\s*(\d+)", line):
                data["bobbleheads"] = int(match.group(1))

        # Репутация
        if line.startswith("Репутация"):
            if idx + 1 < len(lines):
                rep_line = lines[idx + 1]
                if not rep_line.startswith("ID") and not rep_line.startswith("🏵"):
                    data["reputation"] = rep_line.strip()

        # Game ID
        if match := re.search(r"ID(\d+)", line):
            data["game_id"] = int(match.group(1))

        # Информация о рейде
        if "Рейд в" in line:
            data["raid_time"] = line.split(":", 1)[-1].strip()
            if idx + 1 < len(lines):
                raid_line = lines[idx + 1]
                data["raid_location"] = raid_line.strip()
                if match := re.search(r"🕳\+(\d+)", raid_line):
                    data["raid_reward_caps"] = int(match.group(1))
                if match := re.search(r"📦\+(\d+)", raid_line):
                    data["raid_reward_materials"] = int(match.group(1))
                extra = re.sub(r"🕳\+\d+|📦\+\d+", "", raid_line).strip()
                if extra:
                    data["raid_reward_other"] = extra

    # Сохраняем экипировку
    if gear_lines:
        data["gear"] = "\n".join(gear_lines)

    # Проверка наличия game_id
    if not data.get("game_id"):
        if not silent:
            await safe_answer(message, "❌ Не удалось извлечь ID.")
        return

    # Поиск или создание профиля игрока
    profile = session.query(PlayerProfile).filter_by(game_id=data["game_id"]).first()
    if not profile:
        profile = PlayerProfile(game_id=data["game_id"])
        session.add(profile)

    # Обновление полей профиля
    for k, v in data.items():
        setattr(profile, k, v)
    profile.updated_at = datetime.utcnow()

    # Устанавливаем, кто добавил профиль
    if message.from_user.id == data["game_id"]:
        profile.added_by_admin = False
        profile.added_by_admin_id = None
    elif added_by_admin:
        profile.added_by_admin = True
        profile.added_by_admin_id = message.from_user.id

    # Поиск или создание пользователя
    user = session.query(User).filter_by(game_id=data["game_id"]).first()
    if not user:
        user = User(
            game_id=data["game_id"],
            nickname=data.get("nickname") or f"user_{data['game_id']}",
            faction=data.get("faction"),
            squad=data.get("squad"),
        )
        session.add(user)
    else:
        if data.get("nickname"):
            user.nickname = data["nickname"]
        if data.get("faction"):
            user.faction = data["faction"]
        if data.get("squad"):
            user.squad = data["squad"]
        if data.get("role"):
            user.role = data["role"]

    session.commit()

    # Отправляем ответ пользователю, если не требуется молчать
    if not silent:
        await safe_answer(message, f"✅ Профиль <b>{profile.nickname or 'игрока'}</b> обновлён.", parse_mode="HTML")


def extract_nickname_and_game_id(message: Message) -> tuple[str, int] | None:
    # Извлечение никнейма и game_id из сообщения
    text = message.text
    if not text:
        return None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    nickname = None
    game_id = None

    for line in lines:
        # Извлечение никнейма и фракции
        if not nickname and re.search(r",\s+⚛️", line):
            match = re.match(r"(.+),\s+⚛️(.+)", line)
            if match:
                nickname = match.group(1)

        # Извлечение game_id
        if not game_id:
            match = re.search(r"ID(\d+)", line)
            if match:
                game_id = int(match.group(1))

        # Если оба найдены — выходим
        if nickname and game_id:
            return nickname, game_id

    return None
