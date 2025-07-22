import aiosqlite
import asyncio

async def migrate():
    async with aiosqlite.connect('database.sqlite') as db:
        # Добавляем поле name, если его нет
        cursor = await db.execute("PRAGMA table_info(product_requests)")
        columns = [row[1] async for row in cursor]
        if 'name' not in columns:
            print('Добавляю поле name...')
            await db.execute("ALTER TABLE product_requests ADD COLUMN name TEXT")
        if 'filter' not in columns:
            print('Добавляю поле filter...')
            await db.execute("ALTER TABLE product_requests ADD COLUMN filter TEXT")
        if 'cashback' not in columns:
            print('Добавляю поле cashback...')
            await db.execute("ALTER TABLE product_requests ADD COLUMN cashback INTEGER")
        if 'photo_id' not in columns:
            print('Добавляю поле photo_id...')
            await db.execute("ALTER TABLE product_requests ADD COLUMN photo_id TEXT")
        await db.commit()
        print('Миграция завершена.')

if __name__ == "__main__":
    asyncio.run(migrate()) 