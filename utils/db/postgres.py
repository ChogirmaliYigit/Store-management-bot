import calendar
import asyncpg

from typing import Union
from datetime import datetime, timedelta
from asyncpg import Connection
from asyncpg.pool import Pool
from data import config
from utils.notify_admins import logging_to_admin


class Database:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            database=config.DB_NAME,
            port=config.DB_PORT,
        )

    async def execute(
        self,
        command,
        *args,
        fetch: bool = False,
        fetchval: bool = False,
        fetchrow: bool = False,
        execute: bool = False,
    ):

        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
            return result

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join(
            [f"{item} = ${num}" for num, item in enumerate(parameters.keys(), start=1)]
        )
        return sql, tuple(parameters.values())

    async def add_user(self, full_name, username, telegram_id):
        sql = "INSERT INTO users (full_name, username, telegram_id, created_at) VALUES($1, $2, $3, $4) returning *"
        return await self.execute(sql, full_name, username, telegram_id, datetime.now(), fetchrow=True)

    async def add_order(self, area, client_name, client_phone_number, client_products, client_products_images,
                        client_products_wrapping_type, client_wrapped_products_images, client_products_price,
                        client_products_payment_status, client_social_network, employee, delivery_date, location,
                        delivery_type, note, latitude, longitude, is_sent=True):
        sql = """INSERT INTO orders (
            area, client_name, client_phone_number, client_products, client_products_images,
            client_products_wrapping_type, client_wrapped_products_images, client_products_price,
            client_products_payment_status, client_social_network, employee, delivery_date, location,
            delivery_type, note, is_sent, latitude, longitude, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
        ) returning *"""
        return await self.execute(sql, area, client_name, client_phone_number, client_products,
                                  client_products_images, client_products_wrapping_type, client_wrapped_products_images,
                                  client_products_price, client_products_payment_status, client_social_network,
                                  employee, delivery_date, location, delivery_type, note, is_sent, latitude, longitude,
                                  datetime.now(), fetchrow=True)

    async def add_chat(self, chat_id, chat_type):
        sql = "INSERT INTO chats (chat_id, type) VALUES ($1, $2) returning *"
        return await self.execute(sql, chat_id, chat_type, fetchrow=True)

    async def add_admin(self, login, password, telegram_id, is_active=False):
        sql = "INSERT INTO bot_admins (login, password, telegram_id, is_active) VALUES ($1, $2, $3, $4) returning *"
        return await self.execute(sql, login, password, telegram_id, is_active, fetchrow=True)

    async def select_chat(self, **kwargs):
        sql = "SELECT * FROM chats WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_all_chats(self):
        sql = "SELECT * FROM Chats"
        return await self.execute(sql, fetch=True)

    async def select_orders(self):
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sql = "SELECT * FROM orders WHERE created_at >= $1"
        return await self.execute(sql, today_start, fetch=True)

    async def select_all_orders(self):
        return await self.execute("SELECT * FROM orders", fetch=True)

    async def select_monthly_orders(self):
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = calendar.monthrange(current_month_start.year, current_month_start.month)
        next_month_start = (current_month_start + timedelta(days=last_day)).replace(day=1)
        return await self.execute(
            f"SELECT * "
            f"FROM orders "
            f"WHERE created_at "
            f"BETWEEN {current_month_start} "
            f"AND {next_month_start - timedelta(microseconds=1)}",
            fetch=True
        )

    async def select_all_users(self):
        sql = "SELECT * FROM Users"
        return await self.execute(sql, fetch=True)

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_all_bot_admins(self):
        sql = "SELECT * FROM bot_admins"
        return await self.execute(sql, fetch=True)

    async def get_admin(self, telegram_id):
        sql = "SELECT * FROM bot_admins WHERE telegram_id=$1"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM Users"
        return await self.execute(sql, fetchval=True)

    async def count_order_ids(self):
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sql = "SELECT COUNT(id) FROM orders WHERE created_at >= $1"
        return await self.execute(sql, today_start, fetchval=True)

    async def user_is_admin(self, telegram_id):
        sql = "SELECT COUNT(*) FROM bot_admins WHERE telegram_id=$1"
        user = await self.execute(sql, telegram_id, fetchval=True)
        return user > 0

    async def check_login(self, login):
        sql = "SELECT COUNT(*) FROM bot_admins WHERE login=$1"
        user = await self.execute(sql, login, fetchval=True)
        return user > 0

    async def activate_user(self, telegram_id):
        sql = "UPDATE bot_admins SET is_active=True WHERE telegram_id=$1"
        return await self.execute(sql, telegram_id, execute=True)

    async def delete_users(self):
        await self.execute("DELETE FROM Users WHERE TRUE", execute=True)

    async def delete_groups(self):
        try:
            await self.execute("DELETE FROM chats WHERE type=tashkent_group",
                               execute=True)
            await self.execute("DELETE FROM chats WHERE type=regions_group",
                               execute=True)
        except Exception as err:
            await logging_to_admin(err)

    async def delete_admin(self, telegram_id):
        await self.execute("DELETE FROM bot_admins WHERE telegram_id=$1", telegram_id, execute=True)

    async def drop_users(self):
        await self.execute("DROP TABLE Users", execute=True)
