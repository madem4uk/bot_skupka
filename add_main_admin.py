import aiosqlite
import asyncio

async def add_main_admin():
    async with aiosqlite.connect('database.sqlite') as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id, is_main, is_limited) VALUES (?, 1, 0)", (949562,))
        await db.commit()
        print('Главный админ 5524446848 добавлен.')

if __name__ == "__main__":
    asyncio.run(add_main_admin()) 