import aiosqlite
import asyncio

DB_PATH = 'database.sqlite'

async def main():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE admins SET is_main = 0")
        await db.execute("INSERT OR IGNORE INTO admins (user_id, is_main, is_limited) VALUES (949562, 1, 0)")
        await db.execute("UPDATE admins SET is_main = 1, is_limited = 0 WHERE user_id = 949562")
        await db.commit()
        cursor = await db.execute("SELECT user_id, is_main, is_limited FROM admins")
        rows = await cursor.fetchall()
        print("Все админы:")
        for row in rows:
            print(f"user_id={row[0]}, is_main={row[1]}, is_limited={row[2]}")
    print('Операция завершена.')

if __name__ == "__main__":
    asyncio.run(main()) 