from typing import Union
from datetime import datetime

import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool

from data import config


class Database:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            database=config.DB_NAME,
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
                        delivery_type, note, is_sent=True):
        sql = """INSERT INTO orders (
            area, client_name, client_phone_number, client_products, client_products_images,
            client_products_wrapping_type, client_wrapped_products_images, client_products_price,
            client_products_payment_status, client_social_network, employee, delivery_date, location,
            delivery_type, note, is_sent, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
        ) returning *"""
        return await self.execute(sql, area, client_name, client_phone_number, client_products,
                                  client_products_images, client_products_wrapping_type, client_wrapped_products_images,
                                  client_products_price, client_products_payment_status, client_social_network,
                                  employee, delivery_date, location, delivery_type, note, is_sent, datetime.now(),
                                  fetchrow=True)

    async def add_chat(self, chat_id, chat_type):
        sql = "INSERT INTO chats (chat_id, type) VALUES ($1, $2) returning *"
        return await self.execute(sql, chat_id, chat_type, fetchrow=True)

    async def select_chat(self, **kwargs):
        sql = "SELECT * FROM chats WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_all_chats(self):
        sql = "SELECT * FROM Chats"
        return await self.execute(sql, fetch=True)

    async def count_order_ids(self):
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sql = "SELECT COUNT(id) FROM orders WHERE created_at >= $1"
        return await self.execute(sql, today_start, fetchval=True)

    async def select_orders(self):
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sql = "SELECT * FROM orders WHERE created_at >= $1"
        return await self.execute(sql, today_start, fetch=True)

    async def select_all_users(self):
        sql = "SELECT * FROM Users"
        return await self.execute(sql, fetch=True)

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM Users"
        return await self.execute(sql, fetchval=True)

    async def update_user_username(self, username, telegram_id):
        sql = "UPDATE Users SET username=$1 WHERE telegram_id=$2"
        return await self.execute(sql, username, telegram_id, execute=True)

    async def delete_users(self):
        await self.execute("DELETE FROM Users WHERE TRUE", execute=True)

    async def drop_users(self):
        await self.execute("DROP TABLE Users", execute=True)
