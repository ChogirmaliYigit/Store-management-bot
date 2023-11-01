import logging
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.enums.chat_type import ChatType
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.client.session.middlewares.request_logging import logger
from loader import db, bot
from data.config import ADMINS
from utils.extra_datas import make_title
from keyboards.reply.buttons import area_markup
from states.states import UserState

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
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        group = await db.select_chat(chat_id=message.chat.id)
        if not group:
            if "toshkent" in message.chat.title.lower():
                chat_type = "tashkent_group"
            else:
                chat_type = "regions_group"
            await db.add_chat(chat_id=message.chat.id, chat_type=chat_type)
            logging.info(f"{chat_type} added")
    else:
        telegram_id = message.from_user.id
        full_name = message.from_user.full_name
        username = message.from_user.username
        user = None
        try:
            user = await db.add_user(telegram_id=telegram_id, full_name=full_name, username=username)
        except Exception as error:
            logger.info(error)
        if user:
            count = await db.count_users()
            msg = (f"[{make_title(user['full_name'])}](tg://user?id={user['telegram_id']}) bazaga qo'shildi\.\nBazada {count} ta foydalanuvchi bor\.")
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
                logger.info(f"Data did not send to admin: {admin}. Error: {error}")
        await message.answer(f"Yo'nalishlardan birini tanlang 👇", reply_markup=area_markup)
        await state.set_state(UserState.area)
