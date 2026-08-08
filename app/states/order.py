from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
