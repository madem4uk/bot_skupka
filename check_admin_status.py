import aiosqlite
import asyncio

async def check_admin_status():
    async with aiosqlite.connect('database.sqlite') as db:
        # Проверяем всех админов
        cursor = await db.execute('SELECT user_id, is_main, is_limited FROM admins ORDER BY user_id')
        admins = await cursor.fetchall()
        
        print("=== ВСЕ АДМИНЫ В БАЗЕ ===")
        for admin_id, is_main, is_limited in admins:
            print(f"Admin {admin_id}: is_main={is_main}, is_limited={is_limited}")
        
        print("\n=== ПРОВЕРКА КОНКРЕТНЫХ АДМИНОВ ===")
        
        # Проверяем 5524446848
        cursor = await db.execute('SELECT user_id, is_main, is_limited FROM admins WHERE user_id = 5524446848')
        admin1 = await cursor.fetchone()
        if admin1:
            print(f"5524446848: is_main={admin1[1]}, is_limited={admin1[2]}")
        else:
            print("5524446848: НЕ НАЙДЕН В БАЗЕ!")
        
        # Проверяем 6696364473
        cursor = await db.execute('SELECT user_id, is_main, is_limited FROM admins WHERE user_id = 6696364473')
        admin2 = await cursor.fetchone()
        if admin2:
            print(f"6696364473: is_main={admin2[1]}, is_limited={admin2[2]}")
        else:
            print("6696364473: НЕ НАЙДЕН В БАЗЕ!")
        
        # Проверяем, сколько главных админов
        cursor = await db.execute('SELECT COUNT(*) FROM admins WHERE is_main = 1')
        main_count = await cursor.fetchone()
        print(f"\nКоличество главных админов: {main_count[0]}")

if __name__ == "__main__":
    asyncio.run(check_admin_status()) 