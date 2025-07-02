from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from keyboards.location_menu import location_admin_menu
from keyboards.raid_menu import raid_main_menu, raid_admin_menu
from keyboards.main_menu import main_menu_keyboard
from keyboards.admin_menu import (
    full_admin_menu,
    user_admin_menu,
    guidepage_admin_menu,
)
from keyboards.info_menu import info_menu_keyboard

router = Router()


@router.message(F.text.lower().in_(["отмена", "/cancel"]))
async def cancel_fsm(message: Message, state: FSMContext):
    # Получаем данные из текущего состояния FSM (Finite State Machine)
    data = await state.get_data()

    # Извлекаем из данных источник меню, откуда была вызвана FSM
    menu = data.get("from_menu")

    # Очищаем состояние FSM
    await state.clear()

    # Возвращаем пользователя в соответствующее меню в зависимости от источника
    if menu == "raid_admin":
        # Если отмена произошла в админ-меню рейдов — возвращаем туда
        await safe_answer(message, "↩️ Возврат в меню рейдов (админ).", reply_markup=raid_admin_menu())
    elif menu == "raid":
        # Если отмена произошла в меню рейдов — возвращаем туда
        await safe_answer(message,
            "↩️ Возврат в меню рейдов.",
            reply_markup=raid_main_menu(is_admin=(message.from_user.id in ADMIN_IDS)),
        )
    elif menu == "admin":
        # Если отмена произошла в админ-панели — возвращаем в админ-панель
        await safe_answer(message, "↩️ Возврат в админ-панель.", reply_markup=full_admin_menu())
    elif menu == "admin_users":
        # Если отмена произошла в меню пользователей — возвращаем туда
        await safe_answer(message, "↩️ Возврат в меню пользователей.", reply_markup=user_admin_menu())
    elif menu == "admin_guides":
        # Если отмена произошла в меню гайдов — возвращаем туда
        await safe_answer(message, "↩️ Возврат в меню гайдов.", reply_markup=guidepage_admin_menu())
    elif menu == "info":
        # Если отмена произошла в справочном меню — возвращаем туда
        await safe_answer(message, "↩️ Возврат в справочное меню.", reply_markup=info_menu_keyboard())
    elif menu == "admin_locations":
        # Если отмена произошла в меню локаций — возвращаем туда
        await safe_answer(message, "↩️ Возврат в меню локаций.", reply_markup=location_admin_menu())
    else:
        # Если источник не определён — возвращаем в главное меню
        is_admin = message.from_user.id in ADMIN_IDS
        await safe_answer(message, "↩️ Возврат в главное меню.", reply_markup=main_menu_keyboard(is_admin=is_admin))

    # Отправляем сообщение об отмене действия
    await safe_answer(message, "❌ Действие отменено.")
