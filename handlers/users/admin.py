import logging
import asyncio
import asyncpg
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loader import db, bot
from keyboards.inline.buttons import are_you_sure_markup, get_admins_markup
from keyboards.reply.buttons import area_markup
from states.states import AdminState, UserState
from filters.admin import IsBotAdminFilter
from data.config import ADMINS
from utils.pgtoexcel import export_to_excel
from utils.extra_datas import write_orders_to_sheets

router = Router()


@router.message(Command('allusers'), IsBotAdminFilter(ADMINS))
async def get_all_users(message: types.Message):
    users = await db.select_all_users()

    file_path = f"data/users_list.xlsx"
    await export_to_excel(data=users, headings=['ID', 'Full Name', 'Username', 'Telegram ID'], filepath=file_path)

    await message.answer_document(types.input_file.FSInputFile(file_path))


@router.message(Command('reklama'), IsBotAdminFilter(ADMINS))
async def ask_ad_content(message: types.Message, state: FSMContext):
    await message.answer("Reklama uchun post yuboring")
    await state.set_state(AdminState.ask_ad_content)


@router.message(AdminState.ask_ad_content, IsBotAdminFilter(ADMINS))
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
            logging.info(f"Ad did not send to user: {user_id}. Error: {error}")
    await message.answer(text=f"Reklama {count} ta foydalauvchiga muvaffaqiyatli yuborildi.")
    await state.clear()


@router.message(Command('cleandb'), IsBotAdminFilter(ADMINS))
async def ask_are_you_sure(message: types.Message, state: FSMContext):
    msg = await message.reply("Haqiqatdan ham bazani tozalab yubormoqchimisiz?", reply_markup=are_you_sure_markup)
    await state.update_data(msg_id=msg.message_id)
    await state.set_state(AdminState.are_you_sure)


@router.callback_query(AdminState.are_you_sure, IsBotAdminFilter(ADMINS))
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


@router.message(Command("adminlar"), IsBotAdminFilter(ADMINS))
async def admins(message: types.Message, state: FSMContext):
    await message.answer("Adminlar ro'yxati 👇", reply_markup=await get_admins_markup())
    await state.set_state(AdminState.admins)


@router.callback_query(AdminState.admins, IsBotAdminFilter(ADMINS))
async def admins_detailed(call: types.CallbackQuery, state: FSMContext):
    if call.data == "add":
        await call.message.delete()
        await call.message.answer("Yangi admin uchun login yozing:")
        await state.set_state(AdminState.admins_get_login)
    elif call.data.startswith("delete_"):
        try:
            await db.delete_admin(int(call.data.split("_")[-1]))
        except Exception as error:
            logging.error(error)
        await call.answer("Admin o'chirildi!")
        await call.message.edit_reply_markup(reply_markup=await get_admins_markup())
    elif call.data == "main_page":
        await call.message.delete()
        await call.message.answer(f"Yo'nalishlardan birini tanlang 👇", reply_markup=area_markup)
        await state.set_state(UserState.area)


@router.message(AdminState.admins_get_login, IsBotAdminFilter(ADMINS))
async def get_admin_login(message: types.Message, state: FSMContext):
    login = await db.check_login(message.text)
    if login:
        await message.answer("Bu login avval ishlatilgan! Boshqa login kiriting")
    else:
        await state.update_data({"admin_login": message.text})
        await message.answer(text="Endi parolni kiriting:")
        await state.set_state(AdminState.admins_get_password)


@router.message(AdminState.admins_get_password, IsBotAdminFilter(ADMINS))
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
        logging.error(error)
        await message.answer("Admin qo'shishda muammo bo'ldi ❌")
    await state.clear()
    await message.answer("Adminlar ro'yxati 👇", reply_markup=await get_admins_markup())
    await state.set_state(AdminState.admins)


@router.message(Command("excel"), IsBotAdminFilter(ADMINS))
async def get_excel_file(message: types.Message):
    orders = await db.select_all_orders()

    file_path = f"data/orders.xlsx"

    data = [[
        str(order.get("created_at").strftime("%d-%m-%Y")),
        order.get("client_name"),
        order.get("client_phone_number"),
        order.get("client_products"),
        order.get("location") if order.get("location") else "Mavjud emas",
        order.get("delivery_type"),
        order.get("client_products_price"),
        order.get("client_social_network")
    ] for order in orders]
    try:
        await export_to_excel(
            data=data,
            headings=[
                'Sana', 'Ism Familiya', 'Telefon raqami', 'Kitoblar nomi', 'Manzili', 'Yetkazib berish turi',
                "To'lov summasi", 'Ijtimoiy tarmoq'
            ],
            filepath=file_path
        )
        await message.answer_document(types.input_file.FSInputFile(file_path))
    except Exception as excel_error:
        print(excel_error)
        await message.answer("Excel faylga yozishda xatolik yuz berdi.")
        await bot.send_message(ADMINS[0], f"Excel error: {str(excel_error)}")

    # try:
    await write_orders_to_sheets(orders)
    # except Exception as sheets_error:
    #     print(sheets_error)
    #     await message.answer("Sheetsga yozishda xatolik yuz berdi.")
    #     await bot.send_message(ADMINS[0], f"Sheets error: {str(sheets_error)}")
