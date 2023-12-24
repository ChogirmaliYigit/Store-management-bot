from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


area_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Toshkent shahar bo'ylab")],
    [KeyboardButton(text="Viloyatlarga")],
])


skip_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="O'tkazib yuborish")],
])


payment_statuses_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="To'landi ✅")],
    [KeyboardButton(text="To'lanmadi ❌")],
])


social_networks_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Telegram")],
    [KeyboardButton(text="Instagram")],
    [KeyboardButton(text="Telefon orqali")],
    [KeyboardButton(text="Sayt")],
])


employees_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Alfa")],
    [KeyboardButton(text="Betta")],
    [KeyboardButton(text="Gamma")],
    [KeyboardButton(text="Delta")],
])


ask_location_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Lokatsiya tashlash", request_location=True)],
])


agree_location_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Tasdiqlash ✅")],
    [KeyboardButton(text="Qayta jo'natish 🔄", request_location=True)],
])


delivery_types_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Kuryer 👤")],
    [KeyboardButton(text="Yandex 🚕")],
])


agree_order_data_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Tasdiqlash ✅")],
    [KeyboardButton(text="Bekor qilish ❌")],
])


wrapping_types_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="O'rab berish")],
    [KeyboardButton(text="O'ramsiz holat")],
])
