from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from loader import db, bot
from data.config import ADMINS
from utils.extra_datas import make_title
from keyboards.reply.buttons import area_markup
from states.states import UserState, AnonymousUserState
from utils.notify_admins import logging_to_admin

router = Router()


@router.message(CommandStart())
async def do_start(message: types.Message, state: FSMContext):
    """
            MARKDOWN V2                     |     HTML
    link:   [Google](https://google.com/)   |     <a href='https://google.com/'>Google</a>
    bold:   *Qalin text*                    |     <b>Qalin text</b>
    italic: _Yotiq shriftdagi text_         |     <i>Yotiq shriftdagi text</i>



                    **************     Note     **************
    Markdownda _ * [ ] ( ) ~ ` > # + - = | { } . ! belgilari to'g'ridan to'g'ri ishlatilmaydi!!!
    Bu belgilarni ishlatish uchun oldidan \ qo'yish esdan chiqmasin. Masalan  \.  ko'rinishi . belgisini ishlatish uchun yozilgan.
    """
    await state.clear()
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    user = None
    try:
        user = await db.add_user(telegram_id=telegram_id, full_name=full_name, username=username)
    except Exception as error:
        await logging_to_admin(error)
    if user:
        count = await db.count_users()
        msg = (f"[{make_title(user['full_name'])}](tg://user?id={user['telegram_id']}) bazaga qo'shildi\."
               f"\nBazada {count} ta foydalanuvchi bor\.")
    else:
        msg = f"[{make_title(full_name)}](tg://user?id={telegram_id}) bazaga oldin qo'shilgan"
    for admin in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin,
                text=msg,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as error:
            await logging_to_admin(f"Data did not send to admin: {admin}. Error: {error}")
    user = await db.user_is_admin(int(telegram_id))
    admin = await db.get_admin(int(telegram_id))
    if str(telegram_id) in ADMINS or admin.get("is_active"):
        await message.answer(f"Yo'nalishlardan birini tanlang 👇", reply_markup=area_markup)
        await state.set_state(UserState.area)
    elif user:
        await message.answer("Login kiriting:")
        await state.set_state(AnonymousUserState.get_login)


@router.message(AnonymousUserState.get_login)
async def get_login(message: types.Message, state: FSMContext):
    login = await db.check_login(message.text)
    if login:
        await state.update_data({"anonymous_login": message.text})
        await message.answer("Endi parolni kiriting:")
        await state.set_state(AnonymousUserState.get_password)
    else:
        await message.answer("Noto'g'ri login! Qayta kiriting:")


@router.message(AnonymousUserState.get_password)
async def get_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login = data.get("anonymous_login")
    password = message.text
    user = await db.get_admin(int(message.from_user.id))
    if user.get("login") == login and user.get("password") == password:
        await db.activate_user(int(message.from_user.id))
        await message.answer(f"Yo'nalishlardan birini tanlang 👇", reply_markup=area_markup)
        await state.set_state(UserState.area)
    else:
        await message.answer("Login va parol mos kelmadi!")
