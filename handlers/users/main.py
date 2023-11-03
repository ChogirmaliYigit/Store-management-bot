import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.enums.content_type import ContentType
from states.states import UserState
from loader import db, bot
from keyboards.reply.buttons import skip_markup, payment_statuses_markup, social_networks_markup, \
    employees_markup, ask_location_markup, agree_location_markup, delivery_types_markup, agree_order_data_markup, \
    area_markup, wrapping_types_markup
from utils.extra_datas import get_address_by_location, get_state_content, save_state_content

router = Router()


@router.message(F.text.in_({"Toshkent shahar bo'ylab", "Viloyatlarga"}), UserState.area)
async def get_area(message: types.Message, state: FSMContext):
    await state.update_data({"area": message.text})
    await message.answer("Iltimos mijoz ismini kiriting 👤", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(UserState.client_name)


@router.message(UserState.client_name)
async def get_client_name(message: types.Message, state: FSMContext):
    await state.update_data({"client_name": message.text})
    await message.answer("Iltimos mijoz telefon raqamini yuboring 📲")
    await state.set_state(UserState.client_phone_number)


@router.message(UserState.client_phone_number)
async def get_client_phone_number(message: types.Message, state: FSMContext):
    await state.update_data({"client_phone_number": message.text})
    await message.answer("Iltimos mijoz olgan mahsulotlarni yuboring 🛒")
    await state.set_state(UserState.client_products)


@router.message(UserState.client_products)
async def get_client_products(message: types.Message, state: FSMContext):
    await state.update_data({"client_products": message.text})
    await message.answer("Mahsulotning rasmini yuboring 📷\n\n"
                         "<i>Iltimos, rasmlar ko'p bo'lsa bitta bitta yuboring!!!</i>", reply_markup=skip_markup)
    await state.set_state(UserState.client_products_images)


@router.message(UserState.client_products_images)
async def get_client_products_images(message: types.Message, state: FSMContext):
    if message.content_type in [ContentType.PHOTO, ContentType.DOCUMENT]:
        channel = await db.select_chat(type="channel")
        channel = await bot.get_chat(chat_id=channel.get("chat_id"))
        msg = await message.copy_to(chat_id=channel.id)
        data = await state.get_data()
        images = data.get('client_products_images', '')
        images += f"https://t.me/c/{str(channel.id)[4:]}/{msg.message_id}, "
        await state.update_data({
            "client_products_images": images
        })
    elif message.text in ["O'tkazib yuborish"]:
        await message.answer("O'rab berish turini kiriting 🎁", reply_markup=wrapping_types_markup)
        await state.set_state(UserState.client_products_wrapping_type)


@router.message(UserState.client_products_wrapping_type)
async def get_client_products_wrapping_type(message: types.Message, state: FSMContext):
    await state.update_data({"client_products_wrapping_type": message.text})
    if message.text == "O'rab berish":
        await message.answer("Qog'ozning rasmini yuboring 📷\n\n"
                             "<i>Iltimos, rasmlar ko'p bo'lsa bitta bitta yuboring!!!</i>",
                             reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(UserState.client_wrapped_products_images)
    elif message.text == "O'ramsiz holat":
        await message.answer("Iltimos to'lov qiymatini yuboring 💵", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(UserState.client_products_price)


@router.message(UserState.client_wrapped_products_images)
async def get_client_wrapped_products_images(message: types.Message, state: FSMContext):
    if message.content_type in [ContentType.PHOTO, ContentType.DOCUMENT]:
        channel = await db.select_chat(type="channel")
        channel = await bot.get_chat(chat_id=channel.get("chat_id"))
        msg = await message.copy_to(chat_id=channel.id)
        data = await state.get_data()
        images = data.get('client_wrapped_products_images', '')
        images += f"https://t.me/c/{str(channel.id)[4:]}/{msg.message_id}, "
        await state.update_data({
            "client_wrapped_products_images": images
        })
        await message.answer("Yana rasmlar bormi?", reply_markup=skip_markup)
    elif message.text in ["O'tkazib yuborish"]:
        await message.answer("Iltimos to'lov qiymatini yuboring 💵", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(UserState.client_products_price)


@router.message(UserState.client_products_price)
async def get_client_products_price(message: types.Message, state: FSMContext):
    await state.update_data({"client_products_price": message.text})
    data = await state.get_data()
    if data.get("area") != "Viloyatlarga":
        await message.answer("To'lov holati 💸", reply_markup=payment_statuses_markup)
        await state.set_state(UserState.client_products_payment_status)
    else:
        await message.answer("Qaysi tarmoqdan murojaat qildi 🌐", reply_markup=social_networks_markup)
        await state.set_state(UserState.client_social_network)


@router.message(UserState.client_products_payment_status)
async def get_client_products_payment_status(message: types.Message, state: FSMContext):
    await state.update_data({"client_products_payment_status": message.text})
    await message.answer("Qaysi tarmoqdan murojaat qildi 🌐", reply_markup=social_networks_markup)
    await state.set_state(UserState.client_social_network)


@router.message(UserState.client_social_network)
async def get_client_social_network(message: types.Message, state: FSMContext):
    await state.update_data({"client_social_network": message.text})
    await message.answer("Qaysi mutaxassis qabul qildi 👨‍💻", reply_markup=employees_markup)
    await state.set_state(UserState.employee)


@router.message(UserState.employee)
async def get_employee(message: types.Message, state: FSMContext):
    await state.update_data({"employee": message.text})
    await message.answer("Yetkazib berish muddatini yuboring 📅", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(UserState.delivery_date)


@router.message(UserState.delivery_date)
async def get_delivery_date(message: types.Message, state: FSMContext):
    await state.update_data({"delivery_date": message.text})
    data = await state.get_data()
    if data.get("area") == "Viloyatlarga":
        await message.answer("Iltimos manzilni yuboring 📍", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(UserState.location)
    else:
        await message.answer("Iltimos manzilni yuboring yoki lokatsiya tashlang 📍", reply_markup=ask_location_markup)
        await state.set_state(UserState.location)


@router.message(UserState.location)
async def get_location(message: types.Message, state: FSMContext):
    if message.content_type == ContentType.LOCATION:
        location = get_address_by_location(message.location.latitude, message.location.longitude)
    else:
        location = message.text
    await state.update_data({"location": location})
    await message.answer(f"Manzil: {location}", reply_markup=agree_location_markup)
    await state.set_state(UserState.agree_address)


@router.message(UserState.agree_address)
async def ask_agree_address(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "Tasdiqlash ✅":
        if data.get("area") == "Viloyatlarga":
            await message.answer("Izoh qoldiring 🗒", reply_markup=skip_markup)
            await state.set_state(UserState.note)
        else:
            await message.answer("Yetkazib berish turini tanlang 🛵", reply_markup=delivery_types_markup)
            await state.set_state(UserState.delivery_type)
    else:
        if message.content_type == ContentType.LOCATION:
            location = get_address_by_location(message.location.latitude, message.location.longitude)
        else:
            location = message.text
        await state.update_data({"location": location})
        await message.answer(f"Manzil: {location}", reply_markup=agree_location_markup)
        await state.set_state(UserState.agree_address)


@router.message(UserState.delivery_type)
async def get_delivery_type(message: types.Message, state: FSMContext):
    await state.update_data({"delivery_type": message.text})
    await message.answer("Izoh qoldiring 🗒", reply_markup=skip_markup)
    await state.set_state(UserState.note)


@router.message(UserState.note)
async def get_note(message: types.Message, state: FSMContext):
    if message.text != "O'tkazib yuborish":
        await state.update_data({"note": message.text})
    state_content = await get_state_content(state)
    message_to_forward = await message.answer(state_content, reply_markup=agree_order_data_markup,
                                              disable_web_page_preview=True)
    await state.update_data({'message_id_to_forward': message_to_forward.message_id})
    await state.set_state(UserState.agree_order_data)


@router.message(UserState.agree_order_data)
async def ask_agree_order_data(message: types.Message, state: FSMContext):
    if message.text == "Tasdiqlash ✅":
        data = await state.get_data()
        await save_state_content(state)
        channel = None
        if data.get("area") == "Toshkent shahar bo'ylab":
            channel = await db.select_chat(type="tashkent_channel")
        elif data.get("area") == "Viloyatlarga":
            channel = await db.select_chat(type="regions_channel")
        try:
            await bot.forward_message(channel.get('chat_id'), from_chat_id=message.chat.id,
                                      message_id=data.get('message_id_to_forward'))
            await message.answer("Buyurtma kanalga yuborildi ✅")
        except Exception as error:
            logging.error(f"An error occurred while sending order data to the channel ({channel.get('chat_id')}). "
                          f"Error: {error}")
            await message.answer("Kanalga yuborishda muammo tug'ildi ❌")
        await state.clear()
    await message.answer(f"Yo'nalishlardan birini tanlang 👇", reply_markup=area_markup)
    await state.set_state(UserState.area)
