from aiogram.fsm.state import State, StatesGroup


class AddProductState(StatesGroup):
    waiting_product_id = State()
    waiting_name = State()
    waiting_price = State()
    waiting_description = State()
    waiting_image = State()
    waiting_stock = State()


class EditProductState(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_description = State()
    waiting_image = State()
    waiting_stock = State()
