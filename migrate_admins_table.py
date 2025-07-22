import aiosqlite
import asyncio

DB_PATH = 'database.sqlite'

async def migrate():
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли поле is_limited
        cursor = await db.execute("PRAGMA table_info(admins)")
        columns = [row[1] async for row in cursor]
        if 'is_limited' not in columns:
            print('Добавляю поле is_limited...')
            await db.execute("ALTER TABLE admins ADD COLUMN is_limited INTEGER CHECK (is_limited IN (0, 1)) DEFAULT 0")
            await db.commit()
            print('Поле is_limited добавлено.')
        else:
            print('Поле is_limited уже есть.')

if __name__ == '__main__':
    asyncio.run(migrate()) 