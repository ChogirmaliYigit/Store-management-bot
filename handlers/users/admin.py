import asyncio
import asyncpg
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loader import db, bot, update_server_service
from keyboards.inline.buttons import are_you_sure_markup, get_admins_markup
from keyboards.reply.buttons import area_markup
from states.states import AdminState, UserState
from data.config import PULL_COMMAND, RESTART_COMMAND
from utils.pgtoexcel import export_to_excel
from utils.extra_datas import write_orders_to_excel, remove_files_by_pattern, write_sheet_statistics
from utils.notify_admins import logging_to_admin

router = Router()


@router.message(Command('allusers'))
async def get_all_users(message: types.Message):
    users = await db.select_all_users()

    file_path = f"data/users_list.xlsx"
    await export_to_excel(data=users, headings=['ID', 'Full Name', 'Username', 'Telegram ID'], filepath=file_path)

    await message.answer_document(types.input_file.FSInputFile(file_path))


@router.message(Command('reklama'))
async def ask_ad_content(message: types.Message, state: FSMContext):
    await message.answer("Reklama uchun post yuboring")
    await state.set_state(AdminState.ask_ad_content)


@router.message(AdminState.ask_ad_content)
async def send_ad_to_users(message: types.Message, state: FSMContext):
    users = await db.select_all_users()
    count = 0
    for user in users:
        user_id = user[-1]
        try:
            await message.send_copy(chat_id=user_id)
            count += 1
            await asyncio.sleep(0.05)
        except Exception as error:
            await logging_to_admin(f"Ad did not send to user: {user_id}. Error: {error}")
    await message.answer(text=f"Reklama {count} ta foydalauvchiga muvaffaqiyatli yuborildi.")
    await state.clear()


@router.message(Command('cleandb'))
async def ask_are_you_sure(message: types.Message, state: FSMContext):
    msg = await message.reply("Haqiqatdan ham bazani tozalab yubormoqchimisiz?", reply_markup=are_you_sure_markup)
    await state.update_data(msg_id=msg.message_id)
    await state.set_state(AdminState.are_you_sure)


@router.callback_query(AdminState.are_you_sure)
async def clean_db(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    text = ""
    if call.data == 'yes':
        await db.delete_users()
        text = "Baza tozalandi!"
    elif call.data == 'no':
        text = "Bekor qilindi."
    await bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=msg_id)
    await state.clear()


@router.message(Command("adminlar"))
async def admins(message: types.Message, state: FSMContext):
    await message.answer("Adminlar ro'yxati 👇", reply_markup=await get_admins_markup())
    await state.set_state(AdminState.admins)


@router.callback_query(AdminState.admins)
async def admins_detailed(call: types.CallbackQuery, state: FSMContext):
    if call.data == "add":
        await call.message.delete()
        await call.message.answer("Yangi admin uchun login yozing:")
        await state.set_state(AdminState.admins_get_login)
    elif call.data.startswith("delete_"):
        try:
            await db.delete_admin(int(call.data.split("_")[-1]))
        except Exception as error:
            await logging_to_admin(error)
        await call.answer("Admin o'chirildi!")
        await call.message.edit_reply_markup(reply_markup=await get_admins_markup())
    elif call.data == "main_page":
        await call.message.delete()
        await call.message.answer(f"Yo'nalishlardan birini tanlang 👇", reply_markup=area_markup)
        await state.set_state(UserState.area)


@router.message(AdminState.admins_get_login)
async def get_admin_login(message: types.Message, state: FSMContext):
    login = await db.check_login(message.text)
    if login:
        await message.answer("Bu login avval ishlatilgan! Boshqa login kiriting")
    else:
        await state.update_data({"admin_login": message.text})
        await message.answer(text="Endi parolni kiriting:")
        await state.set_state(AdminState.admins_get_password)


@router.message(AdminState.admins_get_password)
async def get_admin_password(message: types.Message, state: FSMContext):
    await state.update_data({"admin_password": message.text})
    await message.answer("Adminning telegram ID'sini kiriting.\n\n<b>ID ni olish uchun @getmy_idbot ga kirib start "
                         "bosishi kerak va bot bergan ID ni yuborishingiz kerak!</b>")
    await state.set_state(AdminState.admins_get_telegram_id)


@router.message(AdminState.admins_get_telegram_id)
async def get_admin_telegram_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        await db.add_admin(data.get("admin_login"), data.get("admin_password"), int(message.text))
        await message.answer("Admin muvaffaqiyatli qo'shildi ✅")
    except asyncpg.exceptions.UniqueViolationError:
        await message.answer("Admin oldin qo'shilgan ℹ️")
    except Exception as error:
        await logging_to_admin(error)
        await message.answer("Admin qo'shishda muammo bo'ldi ❌")
    await state.clear()
    await message.answer("Adminlar ro'yxati 👇", reply_markup=await get_admins_markup())
    await state.set_state(AdminState.admins)


@router.message(F.text.startswith('/excel'))
async def get_excel_file(message: types.Message):
    if len(str(message.text)) > 6:
        month = str(message.text).split()[1].split("-")[0]
        year = str(message.text).split()[1].split("-")[1]
        if not 1 <= int(month) <= 12 or len(year) != 4:
            await message.answer("Iltimos, sanani to'g'ri ko'rinishda bering. Namuna: <code>/excel 12-2023</code>")
            return
    else:
        month = datetime.now().month
        year = datetime.now().year
    file_path = f"data/buyurtmalar_{month}_{year}.xlsx"

    orders = await db.select_monthly_orders(month=month, year=year)

    try:
        await message.answer_document(await write_orders_to_excel(orders, file_path))
    except Exception as excel_error:
        await message.answer("Excel faylga yozishda xatolik yuz berdi.")
        await logging_to_admin(f"Excel error: {str(excel_error)}")


@router.message(Command("excel_full"))
async def get_excel_file(message: types.Message):
    orders = await db.select_all_orders()
    file_path = f"data/buyurtmalar_toliq.xlsx"

    try:
        await message.answer_document(await write_orders_to_excel(orders, file_path))
    except Exception as excel_error:
        await message.answer("Excel faylga yozishda xatolik yuz berdi.")
        await logging_to_admin(f"Excel error: {str(excel_error)}")


@router.message(Command("dbdata"))
async def send_db(message: types.Message):
    file_path = "backend/data.db"
    try:
        await message.answer_document(types.input_file.FSInputFile(file_path))
    except Exception as excel_error:
        await logging_to_admin(f"Data sending error {file_path}: {str(excel_error)}")

    file_path = "backend/data.sql"
    try:
        await message.answer_document(types.input_file.FSInputFile(file_path))
    except Exception as excel_error:
        await logging_to_admin(f"Data sending error {file_path}: {str(excel_error)}")


@router.message(Command("update_server"))
async def update_server(message: types.Message):
    try:
        await update_server_service(PULL_COMMAND, RESTART_COMMAND)
    except Exception as error:
        await logging_to_admin(f"Error while updating the server: {error}")


@router.message(Command("unwritten_orders"))
async def get_unwritten_orders(message: types.Message):
    orders = await db.select_all_unwritten_orders()
    file_path = f"data/unwritten_orders.xlsx"

    try:
        if orders:
            await message.answer_document(await write_orders_to_excel(orders, file_path))
        else:
            await message.answer("There is no orders which has not written to sheets")
    except Exception as excel_error:
        await message.answer("Excel faylga yozishda xatolik yuz berdi.")
        await logging_to_admin(f"Excel error: {str(excel_error)}")


@router.message(Command("delete_files"))
async def delete_files(message: types.Message):
    """
    To delete some files which in the `data` and `backend` directories
    """
    result = remove_files_by_pattern("data", ["*.xlsx"]).strip()
    result += f"\n{remove_files_by_pattern('backend', ['*.db', '*.sql'])}"
    result = result.strip()
    if not result:
        result = "There is no files to remove"
    await message.answer(result)


@router.message(Command("sheets_stats"))
async def write_sheet_stats(message: types.Message):
    try:
        month = int(message.text.split()[1].split('-')[0])
        year = int(message.text.split()[1].split('-')[1])
        await write_sheet_statistics(month, year)
        await message.answer("Successfully written")
    except Exception as e:
        await logging_to_admin(f"Error while writing stats to sheets: {e.__class__.__name__}: {e}")
