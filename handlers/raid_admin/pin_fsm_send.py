from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from pytz import timezone

from states.pin_states import PinFSM
from database.models import User, RaidEvent, RaidPinSendLog, RaidPinData
from database.db import session
from keyboards.cancel import cancel_keyboard
from keyboards.raid_menu import raid_admin_menu

router = Router()

# 📍 Старт выдачи пина: выбор рейда
@router.message(F.text == "📍 Выдать пин для рейда")
async def start_pin_select_raid(message: Message, state: FSMContext):
    data = await state.get_data()
    raid_id = data.get("raid_id")

    await state.update_data(from_menu="raid_admin")  # Для кнопки Отмена

    if raid_id:
        raid = session.query(RaidEvent).filter_by(id=raid_id).first()
        if raid:
            await state.update_data(raid_id=raid.id)
            await state.set_state(PinFSM.km)
            await safe_answer(message, "📍 Введите расстояние до точки (например: 12):", reply_markup=cancel_keyboard())
            return

    # Если raid_id нет — выводим список активных рейдов
    raids = (
        session.query(RaidEvent)
        .filter(RaidEvent.status == "active")
        .order_by(RaidEvent.start_time.asc())
        .all()
    )

    if not raids:
        await safe_answer(message, "❌ Нет активных рейдов для выдачи пина.")
        return

    await state.update_data(raid_choice_list=[r.id for r in raids])
    await state.set_state(PinFSM.select_raid)
    lines = [
        f"{i+1}. {r.name} (ID {r.id}) — {r.start_time.strftime('%d.%m %H:%M')}"
        for i, r in enumerate(raids)
    ]
    await safe_answer(
        message,
        "📋 Активные рейды для пина:\n" +
        "\n".join(lines) +
        "\n\nВведите **номер рейда из списка** (например: 1) или нажмите Отмена.",
        reply_markup=cancel_keyboard()
    )

@router.message(StateFilter(PinFSM.km))
async def pin_enter_km(message: Message, state: FSMContext):
    data = await state.get_data()
    raid_id = data.get("raid_id")
    if not raid_id:
        await safe_answer(message, "⚠️ Не выбран рейд. Начните с команды выдачи пина.")
        await state.clear()
        return

    try:
        km = int(message.text.strip())
        if not (0 <= km <= 100):
            raise ValueError
        await state.update_data(km=km)
        await state.set_state(PinFSM.title)
        await safe_answer(message, "✏️ Введите заголовок пина:", reply_markup=cancel_keyboard())
    except:
        await safe_answer(message, "❌ Введите число от 0 до 100 (например: 12)", reply_markup=cancel_keyboard())


# 📍 Обработка выбора рейда
@router.message(StateFilter(PinFSM.select_raid))
async def pin_select_raid_number(message: Message, state: FSMContext):
    text = message.text.strip()

    # DEBUG: выводим текущее состояние FSM
    data = await state.get_data()
    print(f"[DEBUG] FSM при вводе номера рейда: {data}")

    raid_list = data.get("raid_choice_list")
    if not raid_list:
        await safe_answer(message, "⚠️ Нет активного выбора рейда. Попробуйте заново.")
        await state.clear()
        return

    if not text.isdigit():
        await safe_answer(message, "⚠️ Введите номер рейда (число) или нажмите Отмена.")
        return

    idx = int(text) - 1
    if idx < 0 or idx >= len(raid_list):
        await safe_answer(message, "❌ Неверный номер рейда. Введите корректный номер.")
        return

    raid_id = raid_list[idx]
    await state.update_data(raid_id=raid_id)
    await state.set_state(PinFSM.km)
    await safe_answer(message, "📍 Введите расстояние до точки (например: 12):", reply_markup=cancel_keyboard())

# 📍 Ввод км
@router.message(StateFilter(PinFSM.km))
async def pin_enter_km(message: Message, state: FSMContext):
    try:
        km = int(message.text.strip())
        if not (0 <= km <= 100):
            raise ValueError
        await state.update_data(km=km)
        await state.set_state(PinFSM.title)
        await safe_answer(message, "✏️ Введите заголовок пина:", reply_markup=cancel_keyboard())
    except:
        await safe_answer(message, "❌ Введите число от 0 до 100 (например: 12)", reply_markup=cancel_keyboard())

# 📍 Ввод заголовка
@router.message(StateFilter(PinFSM.title))
async def pin_enter_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(PinFSM.text)
    await safe_answer(message, "💬 Введите подробное описание:", reply_markup=cancel_keyboard())

# 📍 Ввод описания и предпросмотр
@router.message(StateFilter(PinFSM.text))
async def pin_enter_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    data = await state.get_data()
    raid = session.query(RaidEvent).filter_by(id=data.get("raid_id")).first()

    if not raid:
        await safe_answer(message, "❌ Рейд не найден.")
        await state.clear()
        return

    moscow = timezone("Europe/Moscow")
    start_time = raid.start_time
    start_time = moscow.localize(start_time) if start_time.tzinfo is None else start_time.astimezone(moscow)
    raid_dt = start_time.strftime("%d.%m.%Y %H:%M")

    preview = (
        f"<b>{data['title']}</b>\n"
        f"📍 {data['km']} км\n"
        f"🔗 <b>Рейд:</b> {raid.name}\n"
        f"🕓 <b>Время:</b> {raid_dt}\n\n"
        f"{data['description']}"
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Отправить пин")],
            [KeyboardButton(text="✏️ Изменить"), KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )

    await safe_answer(message, f"📤 Предпросмотр пина:\n\n{preview}", parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(PinFSM.confirm)

# 📍 Изменение пина
@router.message(StateFilter(PinFSM.confirm), F.text == "✏️ Изменить")
async def pin_editing(message: Message, state: FSMContext):
    await state.set_state(PinFSM.km)
    await safe_answer(message, "↩️ Начнём заново. Введите расстояние:", reply_markup=cancel_keyboard())


# 📍 Отправка пина
@router.message(StateFilter(PinFSM.confirm), F.text == "✅ Отправить пин")
async def pin_send(message: Message, state: FSMContext):
    data = await state.get_data()
    raid = session.query(RaidEvent).filter_by(id=data.get("raid_id")).first()

    if not raid:
        await safe_answer(message, "❌ Рейд не найден.")
        await state.clear()
        return

    # Сохраняем или обновляем данные пина для рейда
    existing = session.query(RaidPinData).filter_by(raid_id=raid.id).first()
    if existing:
        existing.title = data["title"]
        existing.km = data["km"]
        existing.description = data["description"]
    else:
        session.add(RaidPinData(
            raid_id=raid.id,
            title=data["title"],
            km=data["km"],
            description=data["description"]
        ))
    session.commit()

    squad = raid.squad
    if squad == "ALL_USERS":
        users = session.query(User).all()
    elif squad == "ALL_SQUADS":
        users = session.query(User).filter(User.squad.isnot(None)).all()
    else:
        users = session.query(User).filter(User.squad.in_([s.strip() for s in squad.split(",")])).all()

    pin_text = (
        f"<b>{data['title']}</b>\n"
        f"📍 {data['km']} км\n\n"
        f"{data['description']}"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔ Я иду!", callback_data=f"raid_join_{raid.id}")],
        [InlineKeyboardButton(text="🚫 Я не иду", callback_data=f"raid_leave_{raid.id}")],
        [InlineKeyboardButton(text="🔔 Напомнить", callback_data=f"remind_{raid.id}")]
    ])

    count = 0
    for user in users:
        if user.game_id:
            try:
                await safe_send_message(
                    bot=message.bot,
                    chat_id=user.game_id,
                    text=pin_text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
                log = RaidPinSendLog(
                    admin_id=message.from_user.id,
                    raid_id=raid.id,
                    target_id=user.id,
                    pin_text=pin_text,
                    sent_at=datetime.utcnow(),
                )
                session.add(log)
                count += 1
            except Exception as e:
                print(f"Ошибка отправки пина: {e}")
                continue

    session.commit()
    await safe_answer(message, f"✅ Пин отправлен {count} игрокам.", reply_markup=raid_admin_menu())
    await state.clear()
