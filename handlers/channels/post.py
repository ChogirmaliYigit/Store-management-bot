import logging
from aiogram import Router, types
from loader import db


router = Router()


@router.channel_post()
async def add_channel(message: types.Message):
    if "toshkent" in message.chat.title.lower():
        chat_type = "tashkent_channel"
    elif "foto" in message.chat.title:
        chat_type = "channel"
    else:
        chat_type = "regions_channel"
    channel = await db.select_chat(chat_id=message.chat.id)
    if not channel:
        await db.add_chat(chat_id=message.chat.id, chat_type=chat_type)
        logging.info(f"{chat_type} added")
