from utils.safe_send import safe_answer, safe_send_message
import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database.db import session
from database.models import LocationInfo
from keyboards.cancel import cancel_keyboard
from states.location_states import EditLocationState

router = Router()

def render_location(km: int, loc: LocationInfo | None) -> str:
    # Формирует текстовое представление локации для вывода пользователю
    if not loc:
        return f"📍 <b>{km} км</b>\n\nℹ️ Информация пока не добавлена."
    return f"📍 <b>{km} — {loc.title}</b>\n\n{loc.description}"


@router.message(lambda m: m.text and m.text.startswith("/loc_"))
async def cmd_loc_lookup(message: Message):
    # Обрабатывает команду вида /loc_1234 и отображает информацию о локации
    try:
        code = message.text.lstrip("/").split("@")[0]  # Удаляем префикс "/" и имя бота (если есть)
        if not code.startswith("loc_"):
            return
        km = int(code.replace("loc_", ""))  # Извлекаем номер километра
    except Exception:
        await safe_answer(message, "❌ Неверный формат команды.")
        return

    loc = session.query(LocationInfo).filter_by(km=km).first()
    await safe_answer(message, render_location(km, loc), parse_mode="HTML")


@router.message(F.text.regexp(r"^!\s*(\d+)$").as_("match"))
async def exclam_loc_lookup(message: Message, match: re.Match):
    # Обрабатывает команду вида !1234 и отображает информацию о локации
    km = int(match.group(1))
    loc = session.query(LocationInfo).filter_by(km=km).first()
    await safe_answer(message, render_location(km, loc), parse_mode="HTML")


@router.message(F.text == "✏️ Редактировать локацию")
async def edit_location_start(message: Message, state: FSMContext):
    # Начинает процесс редактирования локации: запрашивает километр
    await state.clear()
    await safe_answer(message, "Введите номер километра для редактирования:", reply_markup=cancel_keyboard())
    await state.set_state(EditLocationState.input_km)


@router.message(EditLocationState.input_km)
async def edit_location_title(message: Message, state: FSMContext):
    # Проверяет, что введён корректный номер километра и запрашивает новое название
    if not message.text.isdigit():
        await safe_answer(message, "❗ Введите число.")
        return

    km = int(message.text)
    loc = session.query(LocationInfo).filter_by(km=km).first()
    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        await state.clear()
        return

    await state.update_data(km=km)
    await safe_answer(message, f"Текущее название: {loc.title}\nВведите новое название (или - чтобы оставить):")
    await state.set_state(EditLocationState.new_title)


@router.message(EditLocationState.new_title)
async def edit_location_description(message: Message, state: FSMContext):
    # Сохраняет новое название и запрашивает новое описание
    await state.update_data(new_title=message.text)
    await safe_answer(message, "Введите новое описание (или - чтобы оставить):")
    await state.set_state(EditLocationState.new_description)


@router.message(EditLocationState.new_description)
async def save_location_edits(message: Message, state: FSMContext):
    # Сохраняет изменения и завершает редактирование
    data = await state.get_data()
    loc = session.query(LocationInfo).filter_by(km=data["km"]).first()

    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
        await state.clear()
        return

    if data["new_title"] != "-":
        loc.title = data["new_title"]
    if message.text != "-":
        loc.description = message.text

    session.commit()
    await safe_answer(message, f"✅ Локация {loc.km} км обновлена.")
    await state.clear()


@router.message(F.text == "🗑 Удалить локацию")
async def delete_location(message: Message, state: FSMContext):
    # Начинает процесс удаления локации: запрашивает километр
    await state.clear()
    await safe_answer(message, "Введите номер километра для удаления:", reply_markup=cancel_keyboard())
    await state.set_state(EditLocationState.input_km)


@router.message(EditLocationState.input_km)
async def confirm_delete_location(message: Message, state: FSMContext):
    # Проверяет, что введён корректный номер километра и удаляет локацию
    if not message.text.isdigit():
        await safe_answer(message, "❗ Введите число.")
        return

    km = int(message.text)
    loc = session.query(LocationInfo).filter_by(km=km).first()

    if not loc:
        await safe_answer(message, "❌ Локация не найдена.")
    else:
        session.delete(loc)
        session.commit()
        await safe_answer(message, f"🗑 Локация {km} км удалена.")
    await state.clear()
