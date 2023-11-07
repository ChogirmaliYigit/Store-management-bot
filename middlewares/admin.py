from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message

from data.config import ADMINS
from loader import db


class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        user = await db.user_is_admin(event.from_user.id)
        if user or str(event.from_user.id) in ADMINS:
            return await handler(event, data)
        return
