import aiosqlite
import asyncio

async def dump():
    async with aiosqlite.connect('database.sqlite') as db:
        print('Таблица users:')
        cursor = await db.execute('SELECT user_id FROM users ORDER BY user_id')
        users = await cursor.fetchall()
        for user in users:
            print(f'User {user[0]}')
        print('\nТаблица admins:')
        cursor = await db.execute('SELECT user_id, is_main, is_limited FROM admins ORDER BY user_id')
        admins = await cursor.fetchall()
        for admin in admins:
            print(f'Admin {admin[0]}: is_main={admin[1]}, is_limited={admin[2]}')

asyncio.run(dump()) 