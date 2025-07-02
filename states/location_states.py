from aiogram.fsm.state import StatesGroup, State


class AddLocationState(StatesGroup):
    # Состояние для выбора способа добавления локации (через пересланное сообщение или вручную)
    choose_method = State()

    # Состояние для получения текста из пересланного сообщения
    forwarded_text = State()

    # Состояние для ввода расстояния в километрах при ручном добавлении
    manual_km = State()

    # Состояние для ввода названия локации при ручном добавлении
    manual_title = State()

    # Состояние для ввода описания локации при ручном добавлении
    manual_description = State()


class EditLocationState(StatesGroup):
    # Состояние для ввода расстояния (километров) локации, которую нужно отредактировать
    input_km = State()

    # Состояние для выбора поля, которое будет изменено (название или описание)
    choose_field = State()

    # Состояние для ввода нового названия локации
    new_title = State()

    # Состояние для ввода нового описания локации
    new_description = State()
