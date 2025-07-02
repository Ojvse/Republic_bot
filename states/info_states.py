from aiogram.fsm.state import StatesGroup, State


class InfoUpdate(StatesGroup):
    # Состояние для ожидания ввода или выбора профиля, который будет обновлен
    awaiting_profile = State()
