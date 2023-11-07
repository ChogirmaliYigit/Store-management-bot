from aiogram.filters.state import StatesGroup, State


class UserState(StatesGroup):
    area = State()
    client_name = State()
    client_phone_number = State()
    client_products = State()
    client_products_images = State()
    client_products_wrapping_type = State()
    client_wrapped_products_images = State()
    client_products_price = State()
    client_products_payment_status = State()
    client_social_network = State()
    employee = State()
    delivery_date = State()
    location = State()
    agree_address = State()
    delivery_type = State()
    note = State()
    agree_order_data = State()


class AdminState(StatesGroup):
    are_you_sure = State()
    ask_ad_content = State()
    admins = State()
    admins_get_login = State()
    admins_get_password = State()
    admins_get_telegram_id = State()


class AnonymousUserState(StatesGroup):
    get_login = State()
    get_password = State()
