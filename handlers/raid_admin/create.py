from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from pytz import timezone

from states.raid_states import RaidEventCreate
from database.models import RaidEvent, User
from database.db import session
from keyboards.cancel import cancel_keyboard
from datetime import datetime, timedelta

router = Router()


@router.message(F.text == "➕ Новый рейд")
async def start_create_raid(message: Message, state: FSMContext):
    # Устанавливаем состояние для ввода названия рейда
    await state.set_state(RaidEventCreate.name)
    # Запрашиваем у пользователя название рейда
    await safe_answer(message, "📛 Введите название рейда:", reply_markup=cancel_keyboard())


@router.message(StateFilter(RaidEventCreate.name))
async def input_name(message: Message, state: FSMContext):
    # Сохраняем введённое название
    await state.update_data(name=message.text.strip())

    # Получаем все уникальные банды из базы данных
    squads = session.query(User.squad).distinct().filter(User.squad.isnot(None)).all()
    squads = [s[0] for s in squads if s[0]]

    # Если банд нет — завершаем процесс
    if not squads:
        await safe_answer(message, "❌ Нет доступных банд в базе.")
        await state.clear()
        return

    # Сохраняем список банд для дальнейшего использования
    await state.update_data(squad_choices=squads)

    # Формируем текст с вариантами выбора банд
    lines = [f"{i+1}. {squad}" for i, squad in enumerate(squads)]
    lines.append("\nВведите номера банд через запятую (напр: 1,3)")
    lines.append("0 — Все банды\n* — Все участники")
    await state.set_state(RaidEventCreate.squad)
    await safe_answer(message, "🦾 Выберите банды для рейда:\n" + "\n".join(lines))


@router.message(StateFilter(RaidEventCreate.squad))
async def input_squad(message: Message, state: FSMContext):
    raw = message.text.strip()
    data = await state.get_data()
    squads = data.get("squad_choices", [])

    # Обрабатываем ввод пользователя
    if raw == "*":
        # Все пользователи
        squad = "ALL_USERS"
    elif raw == "0":
        # Все банды
        squad = "ALL_SQUADS"
    else:
        try:
            indexes = [int(x) for x in raw.split(",")]  # Парсим номера
            selected = [squads[i - 1] for i in indexes if 0 < i <= len(squads)]  # Выбираем нужные банды
            if not selected:
                raise ValueError
            squad = ", ".join(selected)  # Соединяем выбранные банды в строку
        except:
            await safe_answer(message, "⚠️ Неверный формат. Введите номера банд через запятую.")
            return

    # Сохраняем выбранные банды
    await state.update_data(squad=squad)
    await state.set_state(RaidEventCreate.time)
    moscow = timezone('Europe/Moscow')
    current_time = datetime.now(moscow) + timedelta(hours=2)
    example_time = current_time.strftime("%d.%m %H:%M")

    await safe_answer(
        message,
        f"🕔 Введите время начала (например {example_time}):",
        reply_markup=cancel_keyboard()
    )


@router.message(StateFilter(RaidEventCreate.time))
async def input_time(message: Message, state: FSMContext):
    try:
        # Парсим дату и время
        user_input = message.text.strip()
        naive_dt = datetime.strptime(user_input, "%d.%m %H:%M")
        current_year = datetime.now().year
        naive_dt = naive_dt.replace(year=current_year)
        moscow = timezone('Europe/Moscow')
        local_dt = moscow.localize(naive_dt)
    except Exception as e:
        await safe_answer(message, f"⚠️ Неверный формат времени. Пример: 25.06 23:00\nОшибка: {e}")
        return

    data = await state.get_data()
    # Создаём рейд с явным статусом
    new_raid = RaidEvent(
        name=data["name"],
        squad=data["squad"],
        start_time=local_dt,
        status="active"
    )
    session.add(new_raid)
    session.commit()

    # Сохраняем ID созданного рейда в FSM для пина
    await state.update_data(raid_id=new_raid.id)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Выдать пин для рейда")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True,
    )

    msg_time = local_dt.strftime('%d.%m.%Y %H:%M')
    await safe_answer(
        message,
        f"✅ Рейд успешно создан!\n🕓 Старт: {msg_time}\nХотите сразу создать пин для этого рейда?",
        reply_markup=keyboard
    )
    await state.clear()  # Очистили состояние создания рейда
    await state.update_data(raid_id=new_raid.id, from_menu="raid_admin")  # Подготовили данные для пина
