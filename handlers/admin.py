from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.exc import IntegrityError

from config import ADMIN_IDS
from database.db import session
from database.models import User, PlayerProfile
from handlers.fsm_cancel import cancel_fsm
from keyboards.admin_menu import user_admin_menu, full_admin_menu, guidepage_admin_menu
from keyboards.cancel import cancel_keyboard
from keyboards.edit_user import skip_or_cancel_keyboard
from keyboards.location_menu import location_admin_menu
from keyboards.main_menu import main_menu_keyboard
from keyboards.raid_menu import raid_admin_menu
from services.profile_parser_full import parse_full_profile
from states.user_states import AddUser, EditUser
from utils.safe_send import safe_answer

router = Router()


@router.message(F.text == "/access")
async def access_menu(message: Message):
    # Проверяем, является ли пользователь супер-админом
    if message.from_user.id not in ADMIN_IDS:
        await safe_answer(message, "❌ Только супер админ может управлять доступом.")
        return

    # Получаем список всех администраторов из базы данных
    admins = session.query(User).filter_by(is_admin=True).order_by(User.nickname).all()

    # Формируем текстовое представление списка администраторов
    if not admins:
        admin_list = "⛔️ Пока нет администраторов в базе."
    else:
        admin_list = "\n".join([f"• {u.nickname} ({u.game_id})" for u in admins])

    # Отправляем сообщение с меню управления администраторами
    await safe_answer(message,
                      f"🛡 <b>Управление администраторами</b>\n\n"
                      f"{admin_list}\n\n"
                      f"Команды:\n"
                      f"• <code>/set_admin game_id</code> — выдать доступ\n"
                      f"• <code>/unset_admin game_id</code> — снять доступ",
                      parse_mode="HTML"
                      )


@router.message(F.text.in_(["🛠 Админ-панель", "🛠 Админ панель", "/admins_menu"]))
async def admin_panel(message: Message):
    # Получаем ID пользователя и проверяем, есть ли у него права администратора
    user_id = message.from_user.id
    user = session.query(User).filter_by(game_id=user_id).first()
    if user_id not in ADMIN_IDS and not (user and user.is_admin):
        await safe_answer(message, "❌ У вас нет доступа к админ-панели.")
        return

    # Открываем админ-панель с меню
    await safe_answer(message, "🛠 <b>Админ-панель</b>Выберите раздел:", reply_markup=full_admin_menu(),
                      parse_mode="HTML")


@router.message(lambda m: m.text and m.text.startswith("/list_admins"))
async def list_admins(message: Message):
    # Проверка: только супер-админы могут просматривать список админов
    if message.from_user.id not in ADMIN_IDS:
        await safe_answer(message, "❌ Только супер админ может просматривать список админов.")
        return

    # Получаем список всех администраторов
    admins = session.query(User).filter_by(is_admin=True).order_by(User.nickname).all()

    # Если админов нет, отправляем соответствующее сообщение
    if not admins:
        await safe_answer(message, "⛔️ В базе пока нет администраторов.")
        return

    # Формируем и отправляем список админов
    text = "<b>📋 Список администраторов:</b>\n"
    text += "\n".join([f"• {u.nickname} — <code>{u.game_id}</code>" for u in admins])
    await safe_answer(message, text, parse_mode="HTML")


@router.message(lambda m: m.text and m.text.startswith("/admin_help"))
async def admin_help(message: Message):
    # Проверка: только админы могут получить справку
    user_id = message.from_user.id
    user = session.query(User).filter_by(game_id=user_id).first()

    if user_id not in ADMIN_IDS and not (user and user.is_admin):
        await safe_answer(message, "❌ У вас нет доступа к справке администратора.")
        return

    # Формируем справочное сообщение с командами для администраторов
    text = (
        "<b>🛡 Справка для администраторов</b>\n\n"
        "📌 <b>Управление пользователями:</b>\n"
        "• /add_user — добавить игрока вручную\n"
        "• /add_user_forward — добавить из пересланного сообщения\n"
        "• /edit_user &lt;id&gt; — изменить игрока\n"
        "• /remove_user &lt;id&gt; — удалить игрока\n"
        "• /list_users [страница] — список игроков\n"
        "• /info [id/ник] — показать профиль игрока\n\n"
        "📌 <b>Управление администраторами:</b>\n"
        "• /set_admin &lt;id&gt; — выдать права\n"
        "• /unset_admin &lt;id&gt; — снять права\n"
        "• /access — список и управление\n"
        "• /list_admins — текущие админы\n\n"
        "📌 <b>Рейды:</b>\n"
        "• /raid_create — создать рейд\n"
        "• /raid_report — активность за 7 дней\n"
        "• /report — построитель отчётов\n\n"
        "📌 <b>Гайды:</b>\n"
        "• /guide — меню гайдов\n"
        "• /add_guide — добавить\n"
        "• /remove_guide — удалить\n"
        "• /edit_guide — редактировать\n\n"
        "📌 <b>Локации:</b>\n"
        "• /loc_&lt;км&gt; — показать описание (например, /loc_13)\n"
        "• !&lt;км&gt; — аналогичная команда (например, !13)\n\n"
        "🧩 <b>Дополнительно:</b>\n"
        "• /backup_db — резервная копия\n"
        "• /admin_help — эта справка"
    )

    # Отправляем справку
    await safe_answer(message, text, parse_mode="HTML")


@router.message(F.text.startswith("/list_users"))
async def list_users(message: Message):
    # Разбиваем сообщение, чтобы определить номер страницы
    parts = message.text.strip().split()
    page = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 1
    page_size = 20  # Размер страницы
    offset = (page - 1) * page_size  # Сдвиг для пагинации

    # Получаем общее количество пользователей
    total_users = session.query(User).count()

    # Загружаем пользователей на текущей странице
    users = session.query(User).order_by(User.nickname).offset(offset).limit(page_size).all()

    if not users:
        await safe_answer(message, "❌ Пользователи не найдены на этой странице.")
        return

    lines = []
    for u in users:
        # Проверяем, был ли пользователь добавлен админом
        profile = session.query(PlayerProfile).filter_by(game_id=u.game_id).first()
        note = ""
        if profile and profile.added_by_admin:
            admin = None
            if profile.added_by_admin_id:
                admin = session.query(User).filter_by(game_id=profile.added_by_admin_id).first()
            if admin:
                note = f"⚠️ добавлен {admin.nickname}"
            else:
                note = "⚠️ добавлен админом"
        # Формируем строку пользователя
        lines.append(f"• {u.game_id} — {u.nickname} {note}".strip())

    # Вычисляем общее количество страниц
    total_pages = (total_users + page_size - 1) // page_size

    # Отправляем список пользователей
    await safe_answer(
        message,
        f"📋 <b>Пользователи (стр. {page}/{total_pages}):</b>\n" + "\n".join(lines),
        parse_mode="HTML"
    )

    # Если есть следующая страница — предлагаем переход
    if page < total_pages:
        await safe_answer(message, f"➡️ Для следующей страницы: /list_users {page + 1}")


@router.message(F.text == "/add_user_forward")
async def add_user_forward(message: Message):
    # Проверяем, есть ли реплай на сообщение
    if not message.reply_to_message or not message.reply_to_message.text:
        await safe_answer(message, "ℹ️ Используйте эту команду в ответ на сообщение с пип-боем.")
        return

    # Извлекаем никнейм и ID из реплая
    from services.profile_parser_full import extract_nickname_and_game_id
    result = extract_nickname_and_game_id(message.reply_to_message)
    if not result:
        await safe_answer(message, "❌ Не удалось распознать пип-бой.")
        return

    nickname, game_id = result

    # Проверяем, не существует ли уже такой пользователь
    existing = session.query(User).filter_by(game_id=game_id).first()
    if existing:
        await safe_answer(message, "❌ Пользователь уже добавлен.")
        return

    # Создаём нового пользователя
    user = User(game_id=game_id, nickname=nickname)
    session.add(user)
    session.commit()

    # Парсим полный профиль из реплая
    await parse_full_profile(message.reply_to_message, added_by_admin=True)

    await safe_answer(message, f"✅ Пользователь {nickname} добавлен (ID: {game_id}).")


@router.message(F.text == "/add_user")
async def cmd_add_user(message: Message, state: FSMContext):
    # Очищаем предыдущее состояние FSM
    await state.clear()
    # Сохраняем источник вызова (админ-меню)
    await state.update_data(from_menu="admin")
    # Запрашиваем ID игрока
    await safe_answer(message, "Введите ID игрока:", reply_markup=cancel_keyboard())
    await state.set_state(AddUser.game_id)


@router.message(AddUser.game_id)
async def add_game_id(message: Message, state: FSMContext):
    # Проверка на отмену
    if (message.text or "").lower() in ["отмена", "/cancel"]:
        await cancel_fsm(message, state)
        return

    # Проверка: ID должен быть числом
    if not message.text.isdigit():
        await safe_answer(message, "❗ ID должен содержать только цифры. Попробуйте снова:",
                          reply_markup=cancel_keyboard())
        return

    # Сохраняем ID и запрашиваем никнейм
    await state.update_data(game_id=int(message.text))
    await safe_answer(message, "Введите ник:", reply_markup=cancel_keyboard())
    await state.set_state(AddUser.nickname)


@router.message(AddUser.nickname)
async def add_nickname(message: Message, state: FSMContext):
    # Проверка на отмену ввода
    if (message.text or "").lower() in ["отмена", "/cancel"]:
        await cancel_fsm(message, state)
        return

    # Сохраняем никнейм пользователя
    await state.update_data(nickname=message.text)

    # Запрашиваем роль у пользователя
    await safe_answer(message, "Введите роль:", reply_markup=cancel_keyboard())
    await state.set_state(AddUser.role)


@router.message(AddUser.role)
async def add_role(message: Message, state: FSMContext):
    # Проверка на отмену ввода
    if (message.text or "").lower() in ["отмена", "/cancel"]:
        await cancel_fsm(message, state)
        return

    # Сохраняем роль пользователя
    await state.update_data(role=message.text)

    # Получаем все данные из FSM
    data = await state.get_data()

    # Список обязательных полей для добавления пользователя
    required_fields = ["game_id", "nickname", "role"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        # Если какие-то поля не заполнены — сообщаем об этом
        await safe_answer(message, f"❌ Не хватает данных: {', '.join(missing)}. Попробуйте сначала.")
        await state.clear()
        return

    # Создаём нового пользователя
    user = User(
        game_id=data["game_id"],
        nickname=data["nickname"],
        role=data["role"]
    )
    session.add(user)

    try:
        # Сохраняем пользователя в БД
        session.commit()
        # Отправляем подтверждение о добавлении
        await safe_answer(message,
                          f"✅ Пользователь <b>{user.nickname}</b> добавлен.",
                          reply_markup=full_admin_menu(),
                          parse_mode="HTML"
                          )
    except IntegrityError:
        # Обработка ошибки уникальности ID
        session.rollback()
        await safe_answer(message, "❌ Ошибка: пользователь с таким ID уже существует.")

    # Очищаем состояние FSM
    await state.clear()


@router.message(F.text.startswith("/edit_user"))
async def cmd_edit_user(message: Message, state: FSMContext):
    # Разбиваем команду, чтобы получить ID пользователя
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await safe_answer(message, "Использование: /edit_user &lt;game_id&gt;", parse_mode="HTML")
        return

    game_id = int(parts[1])
    # Ищем пользователя по ID
    user = session.query(User).filter_by(game_id=game_id).first()
    if not user:
        await safe_answer(message, "Пользователь не найден.")
        return

    # Сохраняем ID пользователя в состоянии FSM
    await state.update_data(game_id=game_id)
    # Запрашиваем новый никнейм
    await safe_answer(message, f"Текущий ник: {user.nickname}. Новый ник или 'Пропустить':",
                      reply_markup=skip_or_cancel_keyboard())
    await state.set_state(EditUser.nickname)


@router.message(EditUser.nickname)
async def edit_nickname(message: Message, state: FSMContext):
    # Проверка на отмену
    if (message.text or "").lower() in ["отмена", "/cancel"]:
        await cancel_fsm(message, state)
        return

    # Сохраняем новый никнейм, если он указан
    if message.text != "Пропустить":
        await state.update_data(nickname=message.text)

    # Запрашиваем фракцию
    await safe_answer(message, "Фракция или 'Пропустить':", reply_markup=skip_or_cancel_keyboard())
    await state.set_state(EditUser.faction)


@router.message(EditUser.faction)
async def edit_faction(message: Message, state: FSMContext):
    # Проверка на отмену
    if (message.text or "").lower() in ["отмена", "/cancel"]:
        await cancel_fsm(message, state)
        return

    # Сохраняем новую фракцию, если она указана
    if message.text != "Пропустить":
        await state.update_data(faction=message.text)

    # Запрашиваем банду
    await safe_answer(message, "Банда или 'Пропустить':", reply_markup=skip_or_cancel_keyboard())
    await state.set_state(EditUser.squad)


@router.message(EditUser.squad)
async def edit_squad(message: Message, state: FSMContext):
    # Проверка на отмену
    if (message.text or "").lower() in ["отмена", "/cancel"]:
        await cancel_fsm(message, state)
        return

    # Сохраняем новую банду, если она указана
    if message.text != "Пропустить":
        await state.update_data(squad=message.text)

    # Запрашиваем роль
    await safe_answer(message, "Роль или 'Пропустить':", reply_markup=skip_or_cancel_keyboard())
    await state.set_state(EditUser.role)


@router.message(EditUser.role)
async def edit_role(message: Message, state: FSMContext):
    # Проверка на отмену
    if (message.text or "").lower() in ["отмена", "/cancel"]:
        await cancel_fsm(message, state)
        return

    # Сохраняем новую роль, если она указана
    if message.text != "Пропустить":
        await state.update_data(role=message.text)

    # Получаем все данные из FSM
    data = await state.get_data()
    # Ищем пользователя по ID
    user = session.query(User).filter_by(game_id=data["game_id"]).first()
    if not user:
        await safe_answer(message, "Ошибка: пользователь не найден.")
        await state.clear()
        return

    # Обновляем данные пользователя, если они были изменены
    if "nickname" in data:
        user.nickname = data["nickname"]
    if "faction" in data:
        user.faction = data["faction"]
    if "squad" in data:
        user.squad = data["squad"]
    if "role" in data:
        user.role = data["role"]

    # Сохраняем изменения в БД
    session.commit()
    # Отправляем подтверждение об обновлении
    await safe_answer(message, "✅ Данные пользователя обновлены.", reply_markup=full_admin_menu())
    # Очищаем состояние FSM
    await state.clear()


@router.message(F.text.startswith("/remove_user"))
async def cmd_remove_user(message: Message):
    # Разбиваем команду, чтобы получить ID пользователя
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await safe_answer(message, "❗ Введите ID как число. Пример: /remove_user 123456")
        return

    game_id = int(parts[1])
    # Ищем пользователя по ID
    user = session.query(User).filter_by(game_id=game_id).first()
    if not user:
        await safe_answer(message, "Пользователь не найден.")
        return

    # Удаляем пользователя из БД
    session.delete(user)
    session.commit()
    # Отправляем подтверждение об удалении
    await safe_answer(message, "Пользователь удалён.")


@router.message(F.text.startswith("/set_admin"))
async def set_admin(message: Message):
    # Проверка: только админ может использовать эту команду
    if message.from_user.id not in ADMIN_IDS:
        await safe_answer(message, "❌ Только админ может выдавать права.")
        return

    # Разбираем команду
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await safe_answer(message, "❗ Введите ID как число. Пример: /set_admin 123456")
        return

    game_id = int(parts[1])
    # Ищем пользователя по ID
    user = session.query(User).filter_by(game_id=game_id).first()
    if not user:
        await safe_answer(message, "❌ Пользователь не найден.")
        return

    # Выдаем права администратора
    user.is_admin = True
    session.commit()
    # Отправляем подтверждение
    await safe_answer(message, f"✅ {user.nickname} теперь админ.")


@router.message(F.text.startswith("/unset_admin"))
async def unset_admin(message: Message):
    # Проверка: только админ может использовать эту команду
    if message.from_user.id not in ADMIN_IDS:
        await safe_answer(message, "❌ Только главный админ может снимать права.")
        return

    # Разбираем команду
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await safe_answer(message, "❗ Введите ID как число. Пример: /unset_admin 123456")
        return

    game_id = int(parts[1])
    # Ищем пользователя по ID
    user = session.query(User).filter_by(game_id=game_id).first()
    if not user:
        await safe_answer(message, "❌ Пользователь не найден.")
        return

    # Снимаем права администратора
    user.is_admin = False
    session.commit()
    # Отправляем подтверждение
    await safe_answer(message, f"🚫 {user.nickname} больше не админ.")


@router.message(F.text == "👥 Пользователи")
async def submenu_users(message: Message):
    # Открываем меню управления пользователями
    await safe_answer(message, "👥 Управление пользователями:", reply_markup=user_admin_menu())


@router.message(F.text == "📘 Гайды (разделы)")
async def open_guidepage_admin(message: Message):
    # Открываем меню управления гайдами
    await safe_answer(message, "📘 Управление структурой гайдов:", reply_markup=guidepage_admin_menu())


@router.message(F.text == "📅 Рейды")
async def submenu_raids(message: Message):
    # Открываем меню управления рейдами
    await safe_answer(message, "⚔️ Управление рейдами:", reply_markup=raid_admin_menu())


@router.message(F.text == "❓ Справка")
async def submenu_help(message: Message):
    # Открываем справочное меню
    await safe_answer(message, "📖 Все доступные команды: /admin_help")


@router.message(F.text == "⬅️ Назад в админ-панель")
async def back_to_admin_panel(message: Message):
    # Возвращаемся в админ-панель
    await safe_answer(message, "↩️ Назад в админ-панель", reply_markup=full_admin_menu())


@router.message(F.text == "⬅️ Выйти в главное меню")
async def back_to_main_menu(message: Message):
    # Получаем пользователя
    user_id = message.from_user.id
    user = session.query(User).filter_by(game_id=user_id).first()
    is_admin = user_id in ADMIN_IDS or (user and user.is_admin)

    # Открываем главное меню
    await safe_answer(message,
                      "🏠 Главное меню",
                      reply_markup=main_menu_keyboard(is_admin=is_admin)
                      )


@router.message(F.text == "📍 Локации")
async def submenu_locations(message: Message):
    # Открываем меню управления локациями
    await safe_answer(message, "📍 Управление локациями:", reply_markup=location_admin_menu())
