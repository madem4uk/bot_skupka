import aiosqlite
import asyncio

async def fix_main_admin():
    async with aiosqlite.connect('database.sqlite') as db:
        print("Исправляю статус главного админа...")
        
        # Убираем главного админа у всех
        await db.execute('UPDATE admins SET is_main = 0')
        await db.commit()
        print("Убрал главного админа у всех пользователей")
        
        # Назначаем 5524446848 главным админом
        await db.execute('UPDATE admins SET is_main = 1 WHERE user_id = 5524446848')
        await db.commit()
        print("Назначил 5524446848 главным админом")
        
        # Проверяем результат
        cursor = await db.execute('SELECT user_id, is_main, is_limited FROM admins ORDER BY user_id')
        admins = await cursor.fetchall()
        
        print("\n=== РЕЗУЛЬТАТ ===")
        for admin_id, is_main, is_limited in admins:
            print(f"Admin {admin_id}: is_main={is_main}, is_limited={is_limited}")

if __name__ == "__main__":
    asyncio.run(fix_main_admin()) 