from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.db import session
from database.models import User, PlayerProfile
from handlers.info import format_user_info
from keyboards.cancel import cancel_keyboard
from keyboards.info_menu import info_menu_keyboard
from keyboards.main_menu import main_menu_keyboard
from services.profile_parser_full import parse_full_profile, extract_nickname_and_game_id
from states.info_states import InfoUpdate
from utils.safe_send import safe_answer

router = Router()


@router.message(StateFilter(None), F.text == "ℹ️ Инфо")
async def open_info_menu(message: Message):
    # Открывает меню информации, отправляя сообщение с клавиатурой
    await safe_answer(message, "🧾 Информация Выберите действие:", reply_markup=info_menu_keyboard())


@router.message(StateFilter(None), F.text == "🔄 Обновить данные")
async def update_request(message: Message, state: FSMContext):
    # Сбрасывает текущее состояние и запрашивает у пользователя профиль из игры
    await state.clear()
    await state.update_data(from_menu="info")
    await safe_answer(message, "📩 Перешлите сюда сообщение с игровым профилем (из 📟Пип-бой /me) :", reply_markup=cancel_keyboard())
    await state.set_state(InfoUpdate.awaiting_profile)


@router.message(InfoUpdate.awaiting_profile)
async def handle_profile_forward(message: Message, state: FSMContext):
    # Обрабатывает пересланное сообщение с игровым профилем
    if message.text and (message.text or "").lower() in ["отмена", "/cancel"]:
        from handlers.fsm_cancel import cancel_fsm
        await cancel_fsm(message, state)
        return

    extracted = extract_nickname_and_game_id(message)
    if not extracted:
        await safe_answer(message, "❌ Не удалось распознать профиль. Попробуйте ещё раз или нажмите Отмена.")
        return

    profile_nick, game_id = extracted
    user = session.query(User).filter_by(game_id=game_id).first()

    if not user:
        await safe_answer(message, "❌ Игрок с таким ID не зарегистрирован. Обратитесь к администратору.")
        await state.clear()
        return

    await parse_full_profile(message, silent=True)

    if user.nickname.strip().lower() != profile_nick.strip().lower():
        await safe_answer(message,
                          f"⚠️ Ваш игровой ник <b>{profile_nick}</b> не совпадает с зарегистрированным именем <b>{user.nickname}</b>."
                          f"Пожалуйста, сообщите администратору.",
                          parse_mode="HTML"
                          )
    else:
        await safe_answer(message, "✅ Профиль успешно обновлён.")

    await state.clear()
    await open_info_menu(message)


@router.message(F.text.in_(["👤 Мой профиль", "👤 Посмотреть мой профиль"]))
async def show_my_profile(message: Message):
    # Отображает личный профиль пользователя
    user = session.query(User).filter_by(game_id=message.from_user.id).first()
    if not user:
        await safe_answer(message, "❌ Вы не зарегистрированы.")
        return

    profile = session.query(PlayerProfile).filter_by(game_id=user.game_id).first()
    if not profile:
        await safe_answer(message, "ℹ️ Подробный профиль ещё не загружен.")
        return

    await safe_answer(message, format_user_info(user), parse_mode="HTML")


@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    # Возвращает пользователя в главное меню
    await state.clear()
    await safe_answer(message, "↩️ Возврат в главное меню.", reply_markup=main_menu_keyboard())
