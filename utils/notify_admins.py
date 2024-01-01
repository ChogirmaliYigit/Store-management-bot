import inspect

from aiogram import Bot

from data.config import ADMINS


async def on_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            bot_properties = await bot.me()
            await bot.send_message(
                int(admin),
                "\n".join([
                    "<b>Bot ishga tushdi.</b>\n",
                    f"<b>Bot ID:</b> {bot_properties.id}",
                    f"<b>Bot Username:</b> {bot_properties.username}"
                ])
            )
        except Exception as err:
            await logging_to_admin(err)


async def logging_to_admin(error_message):
    from loader import bot

    caller_frame = inspect.currentframe().f_back
    file_name = caller_frame.f_code.co_filename
    line_number = caller_frame.f_lineno

    error_message = f"{file_name}:{line_number} -- {str(error_message)}"

    for i in range(0, len(error_message), 1024):
        await bot.send_message(ADMINS[0], str(error_message)[i:i + 1024], disable_web_page_preview=True)
