from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import bot, db


inline_keyboard = [[
    InlineKeyboardButton(text="✅ Yes", callback_data='yes'),
    InlineKeyboardButton(text="❌ No", callback_data='no')
]]
are_you_sure_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_admins_markup():
    keyboard = [
        [InlineKeyboardButton(text="Qo'shish ➕", callback_data="add")]
    ]

    admins = await db.select_all_bot_admins()
    for admin in admins:
        admin_id = admin.get('telegram_id')
        admin_name = str(admin.get("login"))
        keyboard.append([
            InlineKeyboardButton(text=admin_name, callback_data=str(admin_id)),
            InlineKeyboardButton(text="➖", callback_data=f"delete_{admin_id}")
        ])

    keyboard.append([InlineKeyboardButton(text="Bosh sahifa ", callback_data="main_page")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard, row_width=2)
