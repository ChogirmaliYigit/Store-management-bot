import logging
from aiogram import Router, types
from loader import db


router = Router()


@router.channel_post()
async def add_channel(message: types.Message):
    print(message)
    channel = await db.select_chat(chat_id=message.chat.id)
    if not channel:
        await db.add_chat(chat_id=message.chat.id, chat_type="channel")
        logging.info("Channel added")
