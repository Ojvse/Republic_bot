from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from database.db import session
from database.models import GuidePage, LocationInfo
from keyboards.admin_menu import guidepage_admin_menu
from keyboards.cancel import cancel_keyboard
from keyboards.delete_confirm import delete_confirm_keyboard
from states.guidepage_states import AddGuidePage, EditGuidePage, DeleteGuidePage, GuidePaginationState
from utils.safe_send import safe_answer

router = Router()

# Константы
ITEMS_PER_PAGE = 20  # Количество элементов на странице при отображении гайдов
DELETE_PAGE_SIZE = 20  # Количество элементов для удаления за один раз

# Глобальная переменная для хранения временных данных о гайдах, которые будут удалены
pending_deletions = {}  # Словарь: ключ — ID пользователя, значение — код гайда, который будет удален

# Построение дерева гайдов
def render_guide_tree(parent_code=None, level=0):
    # Запрашиваем все гайды, которые являются дочерними по отношению к указанному родителю
    guides = (
        session.query(GuidePage)
        .filter_by(parent_code=parent_code)  # Фильтруем по коду родителя
        .order_by(GuidePage.created_at)  # Сортируем по дате создания
        .all()
    )
    lines = []
    for guide in guides:
        indent = "  " * level  # Уровень вложенности для отступа
        icon = "📂" if guide.text is None else "📄"  # Иконка: папка (если текста нет) или файл
        lines.append(f"{indent}{icon} {guide.title} — /{guide.code}")  # Добавляем строку в дерево
        lines += render_guide_tree(guide.code, level + 1)  # Рекурсивно добавляем вложенные гайды
    return lines  # Возвращаем список строк дерева


@router.message(F.text == "📚 Гайды")
async def show_guides_menu(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM

    # Получаем только корневые разделы гайдов (без родителей)
    root_guides = session.query(GuidePage).filter_by(parent_code=None).order_by(GuidePage.created_at).all()

    if not root_guides:
        # Если корневых гайдов нет — сообщаем об этом
        await safe_answer(message, "📭 Гайды пока не добавлены.")
        return

    text = "📚 <b>Доступные гайды:</b>\n\n"
    for guide in root_guides:
        # Формируем список корневых гайдов
        text += f"• /{guide.code} — {guide.title}\n"

    text += "\nИспользуйте команды выше для просмотра разделов."
    await safe_answer(message, text, parse_mode="HTML")  # Отправляем пользователю


# Команда /guide
@router.message(F.text == "📘 Гайды (разделы)")
async def open_guide_admin_menu(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM
    await safe_answer(message, "📘 Управление структурой гайдов:",
                      reply_markup=guidepage_admin_menu())  # Открываем админ-меню гайдов


# Добавление гайда
@router.message(lambda m: m.text and "Добавить гайд" in m.text)
async def start_add_page(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM
    await state.update_data(from_menu="admin_guides")  # Сохраняем источник вызова
    await safe_answer(message, "Введите заголовок для гайда:", reply_markup=cancel_keyboard())  # Запрашиваем заголовок
    await state.set_state(AddGuidePage.title)  # Переходим к следующему шагу FSM


@router.message(StateFilter(AddGuidePage.title))
async def input_parent_code(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())  # Сохраняем заголовок

    # Отображаем дерево существующих гайдов для выбора родителя
    lines = render_guide_tree()
    tree_text = "\n".join(lines)

    await safe_answer(message,
                      "Введите <b>код родительского раздела</b> (или <code>-</code> для корня):\n\n" + tree_text,
                      parse_mode="HTML",
                      reply_markup=cancel_keyboard()
                      )
    await state.set_state(AddGuidePage.parent_code)  # Переходим к следующему шагу FSM


@router.message(StateFilter(AddGuidePage.parent_code))
async def input_text(message: Message, state: FSMContext):
    raw = message.text.strip().lstrip("/").split("@")[0]
    parent = None if raw == "-" else raw  # Обрабатываем ввод родителя

    if parent is not None:
        # Проверяем, существует ли указанный родительский раздел
        exists = session.query(GuidePage).filter_by(code=parent).first()
        if not exists:
            await safe_answer(message, "❌ Родитель с таким кодом не найден. Повторите ввод.")
            return

    await state.update_data(parent_code=parent)  # Сохраняем родителя
    await safe_answer(message, "Введите текст (или - если это только раздел):",
                      reply_markup=cancel_keyboard())  # Запрашиваем текст
    await state.set_state(AddGuidePage.text)  # Переходим к следующему шагу FSM


@router.message(StateFilter(AddGuidePage.text))
async def suggest_code(message: Message, state: FSMContext):
    await state.update_data(text=None if message.text.strip() == "-" else message.text.strip())  # Сохраняем текст

    data = await state.get_data()
    parent_code = data["parent_code"] or "root"  # Получаем родительский код

    # Генерируем уникальный код на основе родительского раздела
    existing_codes = session.query(GuidePage.code).filter(
        GuidePage.parent_code == data["parent_code"]
    ).all()

    suffixes = []
    for c in existing_codes:
        parts = c[0].split("_")
        if len(parts) > 1 and parts[0] == parent_code and parts[-1].isdigit():
            suffixes.append(int(parts[-1]))
    next_suffix = max(suffixes) + 1 if suffixes else 0
    suggested = f"{parent_code}_{next_suffix}" if parent_code != "root" else f"g_{next_suffix}"

    await state.update_data(suggested_code=suggested)  # Предлагаем сгенерированный код
    await safe_answer(message,
                      f"Предлагаемый код: <code>{suggested}</code>\n"
                      f"Введите свой или напишите <b>Пропустить</b>, чтобы использовать предложенный.",
                      parse_mode="HTML",
                      reply_markup=cancel_keyboard()
                      )
    await state.set_state(AddGuidePage.code)  # Переходим к следующему шагу FSM


@router.message(StateFilter(AddGuidePage.code))
async def save_page(message: Message, state: FSMContext):
    data = await state.get_data()
    user_code = message.text.strip()
    code = data["suggested_code"] if user_code.lower() in ["пропустить",
                                                           "skip"] else user_code  # Используем введённый или предложенный код

    if session.query(GuidePage).filter_by(code=code).first():
        await safe_answer(message, "❌ Такой код уже существует. Введите другой:")
        return

    # Создаём новый гайд
    page = GuidePage(
        code=code,
        title=data["title"],
        parent_code=data["parent_code"],
        text=data["text"]
    )
    session.add(page)
    session.commit()
    await safe_answer(message, f"✅ Гайд /{page.code} добавлен.")
    await state.clear()
    await safe_answer(message, "↩️ Возврат в меню гайдов:", reply_markup=guidepage_admin_menu())  # Возвращаемся в меню


# Редактирование

@router.message(lambda m: m.text and "Редактировать гайд" in m.text)
async def start_edit(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM
    await state.update_data(from_menu="admin_guides")  # Сохраняем источник вызова

    # Отображаем дерево гайдов для выбора редактируемого
    lines = render_guide_tree()
    if not lines:
        await safe_answer(message, "📭 Гайдов пока нет.")
        return

    text = "<b>Введите код гайда, который хотите изменить:</b>\n\n" + "\n".join(lines)
    await safe_answer(message, text.strip(), parse_mode="HTML", reply_markup=cancel_keyboard())
    await state.set_state(EditGuidePage.target_code)  # Переходим к следующему шагу FSM


@router.message(StateFilter(EditGuidePage.target_code))
async def input_new_title(message: Message, state: FSMContext):
    code = message.text.strip().lstrip("/").split("@")[0]
    page = session.query(GuidePage).filter_by(code=code).first()
    if not page:
        await safe_answer(message, "❌ Гайд с таким кодом не найден. Повторите ввод.")
        return

    await state.update_data(target_code=code)  # Сохраняем код редактируемого гайда
    await safe_answer(message, "Введите новый заголовок (или - чтобы не менять):", reply_markup=cancel_keyboard())
    await state.set_state(EditGuidePage.new_title)  # Переходим к следующему шагу FSM


@router.message(StateFilter(EditGuidePage.new_title))
async def input_new_text(message: Message, state: FSMContext):
    await state.update_data(new_title=message.text.strip())  # Сохраняем новый заголовок
    await safe_answer(message, "Введите новый текст (или - чтобы не менять):", reply_markup=cancel_keyboard())
    await state.set_state(EditGuidePage.new_text)  # Переходим к следующему шагу FSM


@router.message(StateFilter(EditGuidePage.new_text))
async def save_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data.get("target_code")
    page = session.query(GuidePage).filter_by(code=code).first()
    if not page:
        await safe_answer(message, "❌ Гайд не найден.")
        await state.clear()
        return

    # Обновляем заголовок и/или текст гайда
    if data["new_title"] != "-":
        page.title = data["new_title"]
    if message.text.strip() != "-":
        page.text = message.text.strip()

    session.commit()
    await safe_answer(message, f"✅ Гайд /{code} обновлён.")
    await state.clear()
    await safe_answer(message, "↩️ Возврат в меню гайдов:", reply_markup=guidepage_admin_menu())  # Возвращаемся в меню


# Функция для отображения дерева гайдов при удалении (с пагинацией)
def render_delete_tree_page(page: int = 0) -> tuple[str, InlineKeyboardMarkup | None]:
    # Получаем все корневые разделы гайдов (без родителей)
    parents = session.query(GuidePage).filter_by(parent_code=None).order_by(GuidePage.created_at).all()

    # Рассчитываем диапазон элементов на текущей странице
    start = page * DELETE_PAGE_SIZE
    end = start + DELETE_PAGE_SIZE
    visible = parents[start:end]

    lines = []
    for p in visible:
        # Отображаем корневой раздел и его вложенные подкатегории
        lines.append(f"🗂 <b>{p.title}</b> — /{p.code}")
        children = session.query(GuidePage).filter_by(parent_code=p.code).order_by(GuidePage.created_at).all()
        for ch in children:
            lines.append(f"  📄 {ch.title} — /{ch.code}")

    # Формируем текстовое представление дерева
    text = "<b>Введите код гайда, который хотите удалить:</b>\n\n" + "\n".join(lines)

    # Создаём клавиатуру для пагинации
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"del_page:{page - 1}"))
    if end < len(parents):
        buttons.append(InlineKeyboardButton(text="➡️ Далее", callback_data=f"del_page:{page + 1}"))

    kb = InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None
    return text, kb  # Возвращаем текст и клавиатуру


# Обработчик команды "Удалить гайд"
@router.message(lambda m: m.text and "Удалить гайд" in m.text)
async def start_delete(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM
    await state.update_data(from_menu="admin_guides")  # Сохраняем источник вызова
    await state.set_state(DeleteGuidePage.target_code)  # Переходим к следующему шагу FSM
    text, kb = render_delete_tree_page(0)  # Получаем первую страницу дерева
    await safe_answer(message, text, parse_mode="HTML", reply_markup=kb)  # Отправляем пользователю


# Обработчик пагинации при удалении гайдов
@router.callback_query(StateFilter(DeleteGuidePage.target_code), lambda c: c.data.startswith("del_page:"))
async def paginate_delete_tree(callback: CallbackQuery, state: FSMContext):
    # Извлекаем номер страницы из callback
    page = int(callback.data.split(":")[1])
    text, kb = render_delete_tree_page(page)  # Получаем нужную страницу дерева
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)  # Обновляем сообщение
    await callback.answer()  # Подтверждаем обработку callback


# Подтверждение удаления гайда
@router.message(StateFilter(DeleteGuidePage.target_code))
async def confirm_delete_code(message: Message, state: FSMContext):
    # Извлекаем код гайда из сообщения
    code = message.text.strip().lstrip("/").split("@")[0]

    # Ищем гайд по коду
    page = session.query(GuidePage).filter_by(code=code).first()
    if not page:
        await safe_answer(message, "❌ Гайд с таким кодом не найден.")
        return

    # Сохраняем код гайда в глобальной переменной для последующего удаления
    pending_deletions[message.from_user.id] = code
    await safe_answer(
        message,
        f"❗️ Вы уверены, что хотите удалить гайд <b>{page.title}</b> — /{code}?",
        parse_mode="HTML",
        reply_markup=delete_confirm_keyboard  # Отправляем клавиатуру подтверждения
    )
    await state.clear()  # Сбрасываем FSM


# Обработчик подтверждения удаления
@router.message(lambda m: m.text == "✅ Подтвердить удаление")
async def confirm_delete_reply(message: Message, state: FSMContext):
    # Извлекаем код гайда из глобальной переменной
    code = pending_deletions.pop(message.from_user.id, None)
    if not code:
        await safe_answer(message, "❌ Не удалось определить, что удалять.")
        return

    # Ищем гайд по коду
    page = session.query(GuidePage).filter_by(code=code).first()
    if page:
        session.delete(page)  # Удаляем гайд
        session.commit()
        await safe_answer(
            message,
            f"🗑 Гайд <b>{page.title}</b> — /{code} удалён.",
            parse_mode="HTML"
        )
    else:
        await safe_answer(message, f"❌ Гайд /{code} не найден.", parse_mode="HTML")

    await safe_answer(message, "↩️ Возврат в меню гайдов:", reply_markup=guidepage_admin_menu())  # Возвращаемся в меню


# Обработчик отмены удаления
@router.message(lambda m: m.text == "❌ Отмена удаления")
async def cancel_delete_reply(message: Message, state: FSMContext):
    # Удаляем данные из глобальной переменной
    pending_deletions.pop(message.from_user.id, None)
    await safe_answer(message, "↩️ Удаление отменено.", reply_markup=guidepage_admin_menu())  # Возвращаемся в меню


# Список всех гайдов
@router.message(lambda m: m.text and "Список гайдов" in m.text)
async def show_full_guide_list(message: Message):
    text, kb = build_list_tree()  # Получаем список гайдов
    await safe_answer(message, text, parse_mode="HTML", reply_markup=kb)  # Отправляем пользователю


# Построение списка гайдов с пагинацией
LIST_PAGE_SIZE = 20  # Количество элементов на странице


def build_list_tree(page=0):
    # Получаем корневые разделы
    parents = (
        session.query(GuidePage)
        .filter_by(parent_code=None)
        .order_by(GuidePage.created_at)
        .all()
    )

    # Рассчитываем диапазон элементов на текущей странице
    start = page * LIST_PAGE_SIZE
    end = start + LIST_PAGE_SIZE
    visible = parents[start:end]

    lines = []
    for p in visible:
        # Отображаем корневой раздел и его вложенные подкатегории
        lines.append(f"📂 /{p.code} — {p.title}")
        children = (
            session.query(GuidePage)
            .filter_by(parent_code=p.code)
            .order_by(GuidePage.created_at)
            .all()
        )
        for ch in children:
            lines.append(f"  └ 📄 /{ch.code} — {ch.title}")

    # Создаём клавиатуру для пагинации
    kb = []
    if page > 0:
        kb.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_page:{page - 1}"))
    if end < len(parents):
        kb.append(InlineKeyboardButton(text="➡️ Далее", callback_data=f"list_page:{page + 1}"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[kb]) if kb else None
    return "<b>📄 Список всех гайдов:</b>\n\n" + "\n".join(lines), keyboard


#  Функция для создания клавиатуры пагинации
def build_guide_pagination_kb(page: int, total: int, parent_code: str):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"guide:{parent_code}:{page - 1}"))
    if (page + 1) * ITEMS_PER_PAGE < total:
        buttons.append(InlineKeyboardButton(text="➡️ Далее", callback_data=f"guide:{parent_code}:{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None


# Обработчик команд вида "/код"
@router.message(lambda m: m.text and m.text.startswith("/"))
async def handle_any_guide_command(message: Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM

    # Извлекаем код гайда из команды
    code = message.text[1:].split()[0].split("@")[0]

    # Ищем гайд по коду
    page = session.query(GuidePage).filter_by(code=code).first()
    if not page:
        return  # Если гайд не найден, завершаем обработку

    # Получаем дочерние разделы
    children = session.query(GuidePage).filter_by(parent_code=page.code).order_by(GuidePage.created_at).all()

    # Сохраняем текущий раздел и переходим к просмотру
    await state.set_state(GuidePaginationState.browsing)
    await state.update_data(parent_code=page.code)

    # Отображаем первую страницу
    page_index = 0
    sliced = children[page_index * ITEMS_PER_PAGE: (page_index + 1) * ITEMS_PER_PAGE]

    # Формируем текст сообщения
    text = f"<b>{page.title}</b>\n\n"
    if page.text:
        text += f"{page.text.strip()}\n"

    if sliced:
        text += "\n<b>Подкатегории:</b>\n"
        for child in sliced:
            text += f"• /{child.code} — {child.title}\n"

    # Дополнительно: если это раздел "map", добавляем информацию о локациях
    if page.code == "map":
        locations = session.query(LocationInfo).order_by(LocationInfo.km).all()
        if locations:
            text += "\n<b>📍 Информация о локациях:</b>\n\n"
            for loc in locations:
                name = loc.title or f"{loc.km} км"
                emoji = name.strip().split()[0] if name.startswith(("⚡️", "⚠️", "💀", "🏕", "❄️")) else ""
                clean_name = name.replace(emoji, "").strip() if emoji else name
                text += f"▪️ {emoji} {clean_name} ({loc.km} км) — /loc_{loc.km}\n"

    # Создаём клавиатуру пагинации
    kb = build_guide_pagination_kb(page_index, len(children), page.code)
    await safe_answer(message, text.strip(), parse_mode="HTML", reply_markup=kb)


# Обработчик пагинации при просмотре гайдов
@router.callback_query(StateFilter(GuidePaginationState.browsing))
async def paginate_guides(callback: types.CallbackQuery, state: FSMContext):
    # Извлекаем данные из callback
    _, parent_code, page_index_str = callback.data.split(":")
    page_index = int(page_index_str)
    await callback.answer()

    # Получаем текущий раздел и его дочерние подкатегории
    page = session.query(GuidePage).filter_by(code=parent_code).first()
    children = session.query(GuidePage).filter_by(parent_code=parent_code).order_by(GuidePage.created_at).all()

    # Рассчитываем диапазон элементов на текущей странице
    start = page_index * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    sliced = children[start:end]

    # Формируем текст сообщения
    text = f"<b>{page.title}</b>\n\n"
    if sliced:
        text += "<b>Подкатегории:</b>\n"
        for child in sliced:
            text += f"• /{child.code} — {child.title}\n"

    # Дополнительно: если это раздел "map", добавляем информацию о локациях
    if page.code == "map":
        locations = session.query(LocationInfo).order_by(LocationInfo.km).all()
        if locations:
            text += "\n<b>📍 Информация о локациях:</b>\n\n"
            for loc in locations:
                name = loc.title or f"{loc.km} км"
                emoji = name.strip().split()[0] if name.startswith(("⚡️", "⚠️", "💀", "🏕", "❄️")) else ""
                clean_name = name.replace(emoji, "").strip() if emoji else name
                text += f"▪️ {emoji} {clean_name} ({loc.km} км) — /loc_{loc.km}\n"

    # Создаём клавиатуру пагинации
    kb = build_guide_pagination_kb(page_index, len(children), parent_code)
    await callback.message.edit_text(text.strip(), parse_mode="HTML", reply_markup=kb)
