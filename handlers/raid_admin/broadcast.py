from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import StateFilter

from states.raid_states import RaidAlert
from database.db import session
from database.models import User
from keyboards.cancel import cancel_keyboard
from services.navigation import return_to_raid_admin_menu

router = Router()

# Обработчик команды "📢 Рассылка"
@router.message(F.text == "📢 Рассылка")
async def start_broadcast(message: Message, state: FSMContext):
    await state.clear()  # Очистка предыдущего состояния
    await state.update_data(from_menu="raid_admin")  # Запоминаем, откуда пришли
    # Запрашиваем у пользователя текст или изображение для рассылки
    await safe_answer(
        message,
        "📩 Отправьте текст или изображение с подписью для рассылки:",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(RaidAlert.text)  # Переход к следующему шагу — ввод текста


# Обработчик ввода текста/изображения для рассылки
@router.message(StateFilter(RaidAlert.text))
async def input_broadcast_content(message: Message, state: FSMContext):
    content = {}

    # Проверяем тип сообщения (текст или фото)
    if message.photo:
        content["photo_id"] = message.photo[-1].file_id
        content["caption"] = message.caption or ""
    elif message.text:
        content["text"] = message.text.strip()
    else:
        await safe_answer(message, "❗ Поддерживается только текст или фото с подписью.")
        return

    await state.update_data(content=content)  # Сохраняем контент

    # Получаем все уникальные банды из БД
    squads = session.query(User.squad).distinct().filter(User.squad.isnot(None)).all()
    squads = [s[0] for s in squads if s[0]]  # Преобразуем результат в список

    await state.update_data(squad_choices=squads)  # Сохраняем список банд

    # Формируем текст с вариантами выбора банд
    lines = [f"{i+1}. {s}" for i, s in enumerate(squads)]
    lines.append("\nВведите номера банд через запятую (напр: 1,3)")
    lines.append("0 — Все банды\n* — Все пользователи")

    await safe_answer(message, "🎯 Кому отправить рассылку:\n" + "\n".join(lines))
    await state.set_state(RaidAlert.target)  # Переход к выбору целевой аудитории


# Обработчик выбора целевой аудитории
@router.message(StateFilter(RaidAlert.target))
async def send_broadcast(message: Message, state: FSMContext):
    data = await state.get_data()
    content = data.get("content", {})
    squads = data.get("squad_choices", [])

    raw = message.text.strip()

    # Определяем целевую аудиторию на основе ввода пользователя
    if raw == "*":
        users = session.query(User).all()  # Все пользователи
    elif raw == "0":
        users = session.query(User).filter(User.squad.isnot(None)).all()  # Все с бандой
    else:
        try:
            indexes = [int(x) for x in raw.split(",")]  # Парсим номера банд
            selected = [squads[i - 1] for i in indexes if 0 < i <= len(squads)]  # Выбираем нужные банды
            if not selected:
                raise ValueError
            users = session.query(User).filter(User.squad.in_(selected)).all()  # Пользователи выбранных банд
        except:
            await safe_answer(message, "⚠️ Неверный ввод. Используй номера через запятую (например: 1,3)")
            return

    count = 0
    # Отправляем сообщение всем пользователям в списке
    for user in users:
        if user.game_id:
            try:
                if "photo_id" in content:
                    # Если это фото — отправляем его
                    await message.bot.send_photo(
                        chat_id=user.game_id,
                        photo=content["photo_id"],
                        caption=content.get("caption", ""),
                        parse_mode="HTML"
                    )
                else:
                    # Если это текст — отправляем его
                    await safe_send_message(
                        bot=message.bot,
                        chat_id=user.game_id,
                        text=content["text"],
                        parse_mode="HTML"
                    )
                count += 1  # Увеличиваем счётчик успешных отправок
            except Exception as e:
                print(f"[ERROR] Рассылка {user.nickname}: {e}")  # Логируем ошибки

    # Сообщаем о результатах рассылки
    await safe_answer(message, f"✅ Рассылка отправлена {count} игрокам.")
    await state.clear()  # Очищаем состояние
    await return_to_raid_admin_menu(message)  # Возвращаемся в меню администратора
