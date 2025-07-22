import aiosqlite
import asyncio

DB_PATH = 'database.sqlite'

async def migrate():
    async with aiosqlite.connect(DB_PATH) as db:
        user_id = 5524446848
        
        # Добавляем пользователя в таблицу users
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        
        # Добавляем как главного админа
        await db.execute("INSERT OR REPLACE INTO admins (user_id, is_main, is_limited) VALUES (?, 1, 0)", (user_id,))
        
        await db.commit()
        print(f'Пользователь {user_id} добавлен как главный админ')

if __name__ == '__main__':
    asyncio.run(migrate()) 