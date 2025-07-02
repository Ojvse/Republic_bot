from utils.safe_send import safe_answer
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.admin_menu import full_admin_menu
from keyboards.main_menu import main_menu_keyboard
from keyboards.raid_menu import raid_main_menu, raid_admin_menu
from config import ADMIN_IDS
from database.db import session
from database.models import User

# Вспомогательная функция для проверки: является ли пользователь админом
def is_user_admin(user_id: int) -> bool:
    user = session.query(User).filter_by(game_id=user_id).first()
    return user_id in ADMIN_IDS or (user and user.is_admin)

# Возвращает пользователя в главное меню с соответствующим сообщением и клавиатурой
async def return_to_main_menu(message: Message):
    # Определяем, админ ли пользователь
    is_admin = is_user_admin(message.from_user.id)
    await safe_answer(message, "🔙 Возврат в главное меню.", reply_markup=main_menu_keyboard(is_admin=is_admin))

# Возвращает пользователя в меню рейдов, учитывая статус администратора
async def return_to_raid_menu(message: Message):
    # Определяем, админ ли пользователь
    is_admin = is_user_admin(message.from_user.id)
    await safe_answer(message, "⬅️ Назад в меню рейдов.", reply_markup=raid_main_menu(is_admin=is_admin))

# Возвращает пользователя в админское меню управления рейдами
async def return_to_raid_admin_menu(message: Message):
    await safe_answer(message, "⬅️ Назад в управление рейдами.", reply_markup=raid_admin_menu())

# Сообщает пользователю, что невозможно определить предыдущее меню и предлагает использовать /start
async def return_to_unknown(message: Message):
    # Определяем, админ ли пользователь
    is_admin = is_user_admin(message.from_user.id)
    await safe_answer(message, "Я не знаю, куда вас вернуть 😅 Используйте /start", reply_markup=main_menu_keyboard(is_admin=is_admin))

# Возвращает пользователя в предыдущее меню на основе данных из FSMContext
async def return_to_previous_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    menu = data.get("from_menu")

    if menu == "raid_admin":
        await safe_answer(message, "↩️ Возврат в админ-панель.", reply_markup=raid_admin_menu())
    elif menu == "admin":
        await safe_answer(message, "↩️ Возврат в главное админ-меню.", reply_markup=full_admin_menu())
    else:
        # Определяем, админ ли пользователь
        is_admin = is_user_admin(message.from_user.id)
        await safe_answer(message, "↩️ Возврат в главное меню.", reply_markup=main_menu_keyboard(is_admin=is_admin))
