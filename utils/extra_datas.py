import datetime
import ssl
import asyncio
import certifi
import gspread
import aioschedule

from loader import db
from geopy.geocoders import Nominatim
from aiogram.fsm.context import FSMContext
from oauth2client.service_account import ServiceAccountCredentials

ESCAPE_CHARS_MARKDOWN = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']


def make_title(title):
    name = ""
    for letter in title:
        if letter in ESCAPE_CHARS_MARKDOWN:
            name += f'\{letter}'
        else:
            name += letter
    return name


def get_address_by_location(latitude, longitude):
    cafile = certifi.where()
    context = ssl.create_default_context(cafile=cafile)
    geolocator = Nominatim(user_agent="store-management-bot", ssl_context=context)
    location = geolocator.reverse((latitude, longitude), language='uz')
    return location.address


async def save_state_content(state: FSMContext):
    data = await state.get_data()
    area = data.get("area")
    client_name = data.get("client_name")
    client_phone_number = data.get("client_phone_number")
    client_products = data.get("client_products")
    client_products_images = data.get("client_products_images")
    client_products_wrapping_type = data.get("client_products_wrapping_type")
    client_wrapped_products_images = data.get("client_wrapped_products_images")
    client_products_price = data.get("client_products_price")
    client_products_payment_status = data.get("client_products_payment_status")
    client_social_network = data.get("client_social_network")
    employee = data.get("employee")
    delivery_date = data.get("delivery_date")
    location = data.get("location")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    delivery_type = data.get("delivery_type")
    note = data.get("note")

    order = await db.add_order(
        area=area,
        client_name=client_name,
        client_phone_number=client_phone_number,
        client_products=client_products,
        client_products_images=client_products_images,
        client_products_wrapping_type=client_products_wrapping_type,
        client_wrapped_products_images=client_wrapped_products_images,
        client_products_price=client_products_price,
        client_products_payment_status=client_products_payment_status,
        client_social_network=client_social_network,
        employee=employee,
        delivery_date=delivery_date,
        location=location,
        delivery_type=delivery_type,
        note=note,
        latitude=latitude,
        longitude=longitude,
    )
    return order


async def get_state_content(state: FSMContext):
    order = await state.get_data()

    order_id = await db.count_order_ids() + 1

    number_emoji = ""
    for number in str(order_id):
        number_emoji += get_emoji_for_number(number)

    content = (f"{number_emoji}\n\n"
               f"👤 Ism: {order.get('client_name')}\n"
               f"📱 Raqam: {order.get('client_phone_number')}\n"
               f"📦 Mahsulot: {order.get('client_products')}\n")

    if order.get('client_products_wrapping_type'):
        content += f"🎁 O'rab berish turi: {order.get('client_products_wrapping_type')}\n"

    content += f"💲 To'lov qiymati: {order.get('client_products_price')}\n"

    if order.get('client_products_payment_status'):
        content += f"💲 To'lov holati: {order.get('client_products_payment_status')}\n"

    content += (f"🤝 Buyurtma oluvchi: {order.get('employee')}\n"
                f"📅 Yetkazib berish muddati: {order.get('delivery_date')}\n")

    if order.get('delivery_type'):
        content += f"🚖 Yetkazib berish turi:⁉️ {order.get('delivery_type')}\n"
    if order.get('location'):
        content += f"📍 Manzil: {order.get('location')}\n"
    if order.get('note'):
        content += f"💬 Izoh: {order.get('note')}\n"
    if order.get('client_products_images'):
        content += f"📷 Mahsulotlarning rasmlari: {order.get('client_products_images')}\n"
    if order.get('client_wrapped_products_images'):
        content += f"📷 O'rab berilgan mahsulotlarning rasmlari: {order.get('client_wrapped_products_images')}"

    return content


def get_emoji_for_number(number: str):
    string_numbers = {
        "0": "0️⃣",
        "1": "1️⃣",
        "2": "2️⃣",
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        "6": "6️⃣",
        "7": "7️⃣",
        "8": "8️⃣",
        "9": "9️⃣",
    }
    return string_numbers.get(number)


async def write_orders_to_sheets():
    orders = await db.select_monthly_orders()
    today = datetime.datetime.now().strftime("%m-%Y")

    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1-nOg35PRZqXc2DsR-I_vGEZl0Bsm1erXIyjxcWo8JHs/edit"
    scope = [
        "https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(spreadsheet_url)
    spreadsheet.del_worksheet(spreadsheet.worksheet(today))
    worksheets = spreadsheet.worksheets()
    last_sheet = worksheets[-1]
    new_sheet = last_sheet.duplicate(new_sheet_name=today)
    start_index = 2
    for order in orders:
        new_sheet.update(f"A{start_index}", order.get("created_at").strftime("%d-%m-%Y"))
        new_sheet.update(f"B{start_index}", order.get("client_name"))
        new_sheet.update(f"C{start_index}", order.get("client_phone_number"))
        new_sheet.update(f"D{start_index}", order.get("client_products"))
        new_sheet.update(f"F{start_index}", order.get("location") if order.get("location") else "Mavjud emas")
        new_sheet.update(f"G{start_index}", order.get("delivery_type"))
        new_sheet.update(f"H{start_index}", order.get("client_products_price"))
        new_sheet.update(f"I{start_index}", order.get("client_social_network"))
        start_index += 1


async def scheduler():
    aioschedule.every().month.at("00:00").do(write_orders_to_sheets)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
