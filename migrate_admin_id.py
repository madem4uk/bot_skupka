import aiosqlite
import asyncio

DB_PATH = 'database.sqlite'

async def migrate():
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли поле admin_id
        cursor = await db.execute("PRAGMA table_info(products)")
        columns = [row[1] async for row in cursor]
        if 'admin_id' not in columns:
            print('Добавляю поле admin_id в таблицу products...')
            await db.execute("ALTER TABLE products ADD COLUMN admin_id INTEGER")
            await db.commit()
            print('Поле admin_id добавлено.')
        else:
            print('Поле admin_id уже есть.')

if __name__ == '__main__':
    asyncio.run(migrate()) 