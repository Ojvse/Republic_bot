from aiogram.fsm.state import StatesGroup, State


class AddGuidePage(StatesGroup):
    # Состояние для ввода уникального кода страницы гайда
    code = State()

    # Состояние для ввода заголовка страницы гайда
    title = State()

    # Состояние для ввода кода родительской страницы (если есть)
    parent_code = State()

    # Состояние для ввода текстового содержания страницы гайда
    text = State()


class EditGuidePage(StatesGroup):
    # Состояние для просмотра дерева страниц гайда
    browsing_tree = State()

    # Состояние для выбора кода страницы, которую нужно отредактировать
    target_code = State()

    # Состояние для ввода нового заголовка страницы
    new_title = State()

    # Состояние для ввода нового текстового содержания страницы
    new_text = State()


class DeleteGuidePage(StatesGroup):
    # Состояние для выбора кода страницы, которую нужно удалить
    target_code = State()


class GuidePaginationState(StatesGroup):
    # Состояние для навигации по дереву страниц гайда
    browsing = State()

