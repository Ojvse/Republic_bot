from aiogram.fsm.state import StatesGroup, State


class DeleteRaid(StatesGroup):
    # Состояние для ожидания ввода идентификатора рейда, который нужно удалить
    awaiting_raid_id = State()


class RaidAlert(StatesGroup):
    # Состояние для ввода времени проведения рейда
    time = State()

    # Состояние для ввода места сбора участников рейда
    location = State()

    # Состояние для ввода дополнительного текста к оповещению (или '-')
    pin_value = State()

    # Состояние для подтверждения выбора банды, которой будет отправлено оповещение
    confirm = State()

    # Состояние для ввода текста произвольной рассылки
    text = State()

    # Состояние для выбора банды, которой будет отправлена рассылка
    target = State()


class RaidEventCreate(StatesGroup):
    # Состояние для ввода названия события рейда
    name = State()

    # Состояние для выбора банды, которая участвует в рейде
    squad = State()

    # Состояние для ввода времени начала события
    time = State()
