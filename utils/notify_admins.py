from aiogram import Bot

from data.config import ADMINS


async def on_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            bot_properties = await bot.me()
            message = ["<b>Bot ishga tushdi.</b>\n",
                       f"<b>Bot ID:</b> {bot_properties.id}",
                       f"<b>Bot Username:</b> {bot_properties.username}"]
            await bot.send_message(int(admin), "\n".join(message))
        except Exception as err:
            await logging_to_admin(err)


async def logging_to_admin(error_message):
    from loader import bot

    await bot.send_message(ADMINS[0], str(error_message))
