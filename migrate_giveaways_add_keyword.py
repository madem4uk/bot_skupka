import asyncio
import aiosqlite

async def migrate():
    async with aiosqlite.connect('database.sqlite') as db:
        try:
            await db.execute("ALTER TABLE giveaways ADD COLUMN keyword TEXT")
            print("Поле keyword добавлено в giveaways!")
        except Exception as e:
            print(f"Возможно, поле уже есть или другая ошибка: {e}")
        await db.commit()

if __name__ == "__main__":
    asyncio.run(migrate()) 