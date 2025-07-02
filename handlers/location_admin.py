from utils.safe_send import safe_answer, safe_send_message
import re
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from database.db import session
from database.models import LocationInfo
from keyboards.location_menu import location_admin_menu
from states.location_states import AddLocationState
from keyboards.cancel import cancel_keyboard

router = Router()

# Шаг 1: выбор метода добавления локации
@router.message(F.text == "📍 Добавить локацию")
async def ask_add_method(message: Message, state: FSMContext):
    # Отображает меню для выбора способа добавления локации
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Ввести вручную"), KeyboardButton(text="📨 Переслать сообщение")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    await state.clear()
    await safe_answer(message, "Как вы хотите добавить локацию?", reply_markup=kb)
    await state.set_state(AddLocationState.choose_method)

# Шаг 2А: ручной ввод локации
@router.message(F.text == "✏️ Ввести вручную")
async def manual_input_km(message: Message, state: FSMContext):
    # Запрашивает номер километра
    await safe_answer(message, "Введите номер километра:", reply_markup=cancel_keyboard())
    await state.set_state(AddLocationState.manual_km)

@router.message(AddLocationState.manual_km)
async def manual_input_title(message: Message, state: FSMContext):
    # Проверяет корректность ввода и запрашивает заголовок
    if not message.text.isdigit():
        await safe_answer(message, "Введите число.")
        return
    await state.update_data(km=int(message.text))
    await safe_answer(message, "Введите заголовок локации:", reply_markup=cancel_keyboard())
    await state.set_state(AddLocationState.manual_title)

@router.message(AddLocationState.manual_title)
async def manual_input_description(message: Message, state: FSMContext):
    # Запрашивает описание локации
    await state.update_data(title=message.text)
    await safe_answer(message, "Введите описание локации:", reply_markup=cancel_keyboard())
    await state.set_state(AddLocationState.manual_description)

@router.message(AddLocationState.manual_description)
async def manual_save(message: Message, state: FSMContext):
    # Сохраняет данные о новой локации
    await state.update_data(description=message.text)
    data = await state.get_data()

    existing = session.query(LocationInfo).filter_by(km=data["km"]).first()
    if existing:
        await safe_answer(message, "❌ Локация на этом км уже есть. Используйте редактирование.")
        await state.clear()
        return

    loc = LocationInfo(
        km=data["km"],
        title=data["title"],
        description=data["description"]
    )
    session.add(loc)
    session.commit()
    await safe_answer(message, f"✅ Локация {data['km']} км добавлена.")
    await state.clear()

# Шаг 2Б: добавление через пересланное сообщение
@router.message(F.text == "📨 Переслать сообщение")
async def wait_forwarded_location(message: Message, state: FSMContext):
    # Начинает процесс добавления локации из пересланного сообщения
    await state.clear()
    await state.update_data(from_menu="admin_locations")
    await safe_answer(message, "Перешлите сообщение с описанием локации.", reply_markup=cancel_keyboard())
    await state.set_state(AddLocationState.forwarded_text)

@router.message(AddLocationState.forwarded_text)
async def handle_forwarded_location(message: Message, state: FSMContext):
    # Обрабатывает пересланное сообщение и извлекает данные о локации
    text = message.text or message.caption or ""
    cleaned = re.sub(r"#\S+", "", text)  # Удаляем хэштеги

    km_match = re.search(r"(\d{1,3})\s*км", cleaned)
    title_match = re.match(r"[^\n\(]{3,}", cleaned.strip())

    if not km_match:
        await safe_answer(message, "❌ Не удалось найти номер километра (например, '27 км'). Или добавьте локации вручную.")
        return

    km = int(km_match.group(1))
    title = title_match.group(0).strip().split("\n")[0] if title_match else f"{km} км"
    description = cleaned.replace(title, "", 1).strip()

    existing = session.query(LocationInfo).filter_by(km=km).first()
    if existing:
        await state.update_data(from_menu="admin_locations")
        await safe_answer(message, "❌ Локация на этом км уже есть. Используйте редактирование.")
        await state.clear()
        return

    loc = LocationInfo(km=km, title=title, description=description)
    session.add(loc)
    session.commit()

    await state.clear()
    await safe_answer(message,
        f"✅ Локация {km} км ({title}) добавлена.",
        reply_markup=location_admin_menu()
    )

# Отображение списка локаций
@router.message(F.text == "📄 Список локаций")
async def list_locations(message: Message):
    # Отображает список всех сохранённых локаций
    locations = session.query(LocationInfo).order_by(LocationInfo.km).all()
    if not locations:
        await safe_answer(message, "📭 Локации не найдены.")
        return

    lines = [f"{loc.km} км — {loc.title}" for loc in locations]
    await safe_answer(message, "<b>📍 Список локаций:</b>\n\n" + "\n".join(lines), parse_mode="HTML")

# Редактирование локации
from states.location_states import EditLocationState

@router.message(F.text == "✏️ Редактировать локацию")
async def start_edit_location(message: Message, state: FSMContext):
    # Начинает процесс редактирования локации
    await state.clear()
    await state.update_data(from_menu="admin_locations")

    locations = session.query(LocationInfo).order_by(LocationInfo.km.desc()).limit(10).all()
    if not locations:
        await safe_answer(message, "📭 Локаций пока нет.")
        return

    lines = [f"• {loc.km} км — {loc.title} (/edit_loc_{loc.km})" for loc in locations]
    text = "<b>Выберите локацию для редактирования:</b>\n\n" + "\n".join(lines)
    text += "\n\nИли введите номер километра вручную:"

    await safe_answer(message, text, parse_mode="HTML", reply_markup=cancel_keyboard())
    await state.set_state(EditLocationState.input_km)

@router.message(F.text.regexp(r"^/edit_loc_(\d{1,3})$").as_("match"))
async def trigger_edit_by_command(message: Message, match: re.Match, state: FSMContext):
    # Обрабатывает команду /edit_loc_... и открывает меню редактирования
    km = int(match.group(1))
    loc = session.query(LocationInfo).filter_by(km=km).first()
    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        return

    await state.clear()
    await state.update_data(km=km, from_menu="admin_locations")
    await state.set_state(EditLocationState.choose_field)

    await safe_answer(message,
        f"📝 <b>{loc.km} км — {loc.title}</b>\n"
        f"Описание:\n\n{loc.description}\n\n"
        "Что вы хотите изменить?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Заголовок"), KeyboardButton(text="📄 Описание")],
                [KeyboardButton(text="❌ Отмена")],
            ],
            resize_keyboard=True
        )
    )

@router.message(EditLocationState.choose_field)
async def handle_field_choice(message: Message, state: FSMContext):
    # Обрабатывает выбор поля для редактирования
    text = message.text.strip()
    data = await state.get_data()
    loc = session.query(LocationInfo).filter_by(km=data["km"]).first()
    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        await state.clear()
        return

    if text == "📝 Заголовок":
        await safe_answer(message, "Введите новый заголовок (или '-' чтобы не менять):", reply_markup=cancel_keyboard())
        await state.set_state(EditLocationState.new_title)

    elif text == "📄 Описание":
        await safe_answer(message,
            f"Текущее описание:\n\n{loc.description}\n\n"
            "Введите новое описание (или '-' чтобы не менять):",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(EditLocationState.new_description)

    elif text == "❌ Отмена":
        await state.clear()
        await safe_answer(message, "↩️ Отменено", reply_markup=location_admin_menu())

    else:
        await safe_answer(message, "Пожалуйста, выберите действие кнопкой.")

@router.message(EditLocationState.new_title)
async def save_new_title(message: Message, state: FSMContext):
    # Сохраняет новый заголовок локации
    title = message.text.strip()
    data = await state.get_data()
    loc = session.query(LocationInfo).filter_by(km=data["km"]).first()
    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        await state.clear()
        return

    if title != "-":
        loc.title = title
        session.commit()

    await state.clear()
    await safe_answer(message, f"✅ Заголовок локации {loc.km} км обновлён.", reply_markup=location_admin_menu())

@router.message(EditLocationState.input_km)
async def ask_new_description(message: Message, state: FSMContext):
    # Проверяет корректность введённого номера км и запрашивает описание
    if not message.text.isdigit():
        await safe_answer(message, "Введите число.")
        return

    km = int(message.text)
    loc = session.query(LocationInfo).filter_by(km=km).first()
    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        await state.clear()
        return

    await state.update_data(km=km)
    await safe_answer(message,
        f"📝 Текущий заголовок: <b>{loc.title}</b>\n"
        f"Текущее описание:\n\n{loc.description}\n\n"
        f"Введите <b>новое описание</b> (или '-' чтобы не менять):",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(EditLocationState.new_description)

@router.message(EditLocationState.new_description)
async def save_new_description(message: Message, state: FSMContext):
    # Сохраняет новое описание локации
    data = await state.get_data()
    loc = session.query(LocationInfo).filter_by(km=data["km"]).first()
    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        await state.clear()
        return

    if message.text.strip() != "-":
        loc.description = message.text.strip()
        session.commit()

    await state.clear()
    await safe_answer(message, f"✅ Локация {loc.km} км обновлена.", reply_markup=location_admin_menu())

# Удаление локации
class DeleteLocationState(StatesGroup):
    km = State()

@router.message(F.text == "🗑 Удалить локацию")
async def start_delete_location(message: Message, state: FSMContext):
    # Начинает процесс удаления локации
    await state.clear()
    await state.update_data(from_menu="admin_locations")
    await safe_answer(message, "Введите номер километра для удаления:", reply_markup=cancel_keyboard())
    await state.set_state(DeleteLocationState.km)

@router.message(DeleteLocationState.km)
async def confirm_delete_location(message: Message, state: FSMContext):
    # Подтверждает удаление локации по указанному км
    if not message.text.isdigit():
        await safe_answer(message, "Введите число.")
        return

    km = int(message.text)
    loc = session.query(LocationInfo).filter_by(km=km).first()
    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        await state.clear()
        return

    session.delete(loc)
    session.commit()
    await state.clear()
    await safe_answer(message, f"🗑 Локация {km} км удалена.", reply_markup=location_admin_menu())
