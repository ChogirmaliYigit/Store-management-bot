import os
import fnmatch
import ssl
import certifi
import gspread
from datetime import datetime
from dateutil.relativedelta import relativedelta
from environs import Env
from aiogram.fsm.context import FSMContext
from geopy.geocoders import Nominatim
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import types
from utils.notify_admins import logging_to_admin
from utils.pgtoexcel import export_to_excel
from loader import db

ESCAPE_CHARS_MARKDOWN = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

env = Env()
env.read_env()


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


def get_spreadsheet():
    spreadsheet_url = env.str("SHEET_URL")
    scope = [
        "https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
    client = gspread.authorize(credentials)

    return client.open_by_url(spreadsheet_url)


def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list)+1)


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

    # Save an order to database if it is not for test
    if "test" not in data.get("client_products"):
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
    else:
        order = {}
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


async def write_orders_to_excel(orders: list, file_path: str):
    data = [[
        str(order.get("created_at").strftime("%d-%m-%Y")),
        order.get("client_name"),
        order.get("client_phone_number"),
        order.get("client_products"),
        order.get("location") if order.get("location") else "Mavjud emas",
        order.get("delivery_type"),
        order.get("client_products_price"),
        order.get("client_social_network"),
        order.get("employee"),
    ] for order in orders if "test" not in order.get("client_products")]

    await export_to_excel(
        data=data,
        headings=[
            'Sana', 'Ism Familiya', 'Telefon raqami', 'Kitoblar nomi', 'Manzili', 'Yetkazib berish turi',
            "To'lov summasi", 'Ijtimoiy tarmoq', "Kim qabul qildi",
        ],
        filepath=file_path
    )
    return types.input_file.FSInputFile(file_path)


async def write_order_to_sheets():
    """
    Write every order to google sheets.
    """
    order = await db.select_unwritten_order()
    if order:
        try:
            sheet_name = order.get("created_at").strftime("%m-%Y")
            spreadsheet = get_spreadsheet()
            sheet = None
            try:
                sheet = spreadsheet.worksheet(sheet_name)
            except Exception as err:
                await logging_to_admin(f"Sheets error while getting sheet by name: "
                                       f"{err.__class__.__name__}: {str(err)}")
            if not sheet:
                sheet = spreadsheet.worksheet("Example").duplicate(new_sheet_name=sheet_name)
            start_index = int(next_available_row(sheet))
            sheet.update(f"A{start_index}", order.get("created_at").strftime("%d-%m-%Y %H:%M:%S"))
            sheet.update(f"B{start_index}", order.get("client_name"))
            sheet.update(f"C{start_index}", order.get("client_phone_number"))
            sheet.update(f"D{start_index}", order.get("client_products"))
            sheet.update(f"E{start_index}", order.get("location") if order.get("location") else "Mavjud emas")
            sheet.update(f"F{start_index}", order.get("delivery_type"))
            sheet.update(f"G{start_index}", order.get("client_products_price"))
            sheet.update(f"H{start_index}", order.get("client_social_network"))
            sheet.update(f"I{start_index}", order.get("employee"))
            await db.mark_order_as_written(order.get("id"))
        except Exception as sheets_error:
            await logging_to_admin(f"Sheets error: {sheets_error.__class__.__name__}: {str(sheets_error)}\n"
                                   f"\nOrder ID: {order.get('id')}")


async def write_sheet_statistics(month: int = None, year: int = None):
    today = datetime.now()
    previous_month = today - relativedelta(months=1)
    if not month:
        month = previous_month.month
    if not year:
        year = previous_month.year
    spreadsheet = get_spreadsheet()
    sheet = None
    sheet_name = f"{month}-{year}"
    if 1 <= month <= 9:
        sheet_name = f"0{sheet_name}"
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except Exception as err:
        await logging_to_admin(f"Sheets error while getting sheet by name: "
                               f"{err.__class__.__name__}: {str(err)}")

    if sheet:
        orders = await db.select_monthly_orders(month=month, year=year)
        total_price = 0
        employees = {}
        for order in orders:
            try:
                price = str(order.get("client_products_price", ""))
                if price.isdigit():
                    price = price.replace(" ", "").replace(".", "")
                    total_price += int(price)
            except Exception as e:
                await logging_to_admin(f"Error while calculating total order price: {e.__class__.__name__}: {e}")
            if employees.get(order.get("employee", None), None):
                employees[order.get("employee")] += 1
            else:
                employees[order.get("employee")] = 1

        employees_text = ""
        for employee, orders_count in employees.items():
            employees_text += f"{employee.title()}: {orders_count} ta\n"

        if orders:
            start_index = int(next_available_row(sheet)) + 10

            sheet.merge_cells(name=f"A{start_index}:B{start_index+1}")
            sheet.update(f"A{start_index}", f"Umumiy summa: {total_price}")

            start_index += 2
            sheet.merge_cells(name=f"A{start_index}:B{start_index + 1}")
            sheet.update(f"A{start_index}", f"Buyurtma qabul qiluvchilar:\n{employees_text.strip()}")


def get_files_in_directory(directory_path):
    return [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]


def remove_files_by_pattern(directory_path, patterns):
    result = ""
    files_to_remove = []

    for pattern in patterns:
        files_to_remove.extend(fnmatch.filter(get_files_in_directory(directory_path), pattern))

    for file_name in files_to_remove:
        file_path = os.path.join(directory_path, file_name)
        os.remove(file_path)
        result += f"Removed: {file_path}\n"
    return result
