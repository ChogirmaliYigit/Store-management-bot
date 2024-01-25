import os
import subprocess
from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from utils.db.postgres import Database
from data.config import BOT_TOKEN

db = Database()
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)


async def update_server_service(pull_command, restart_command):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(f"cd {script_directory} && {pull_command}", shell=True)
    subprocess.run(restart_command, shell=True)
