import aiosqlite
import asyncio

async def check_schema():
    async with aiosqlite.connect('database.sqlite') as db:
        # Проверяем структуру таблицы admins
        cursor = await db.execute("PRAGMA table_info(admins)")
        columns = await cursor.fetchall()
        print('Структура таблицы admins:')
        for col in columns:
            print(f'  {col[1]} {col[2]} {"NOT NULL" if col[3] else ""} {"PRIMARY KEY" if col[5] else ""}')
        
        # Проверяем ограничения
        cursor = await db.execute("PRAGMA foreign_key_list(admins)")
        fks = await cursor.fetchall()
        print('\nForeign keys:')
        for fk in fks:
            print(f'  {fk}')
        
        # Проверяем индексы
        cursor = await db.execute("PRAGMA index_list(admins)")
        indexes = await cursor.fetchall()
        print('\nИндексы:')
        for idx in indexes:
            print(f'  {idx}')
        
        # Проверяем структуру таблицы product_requests
        cursor = await db.execute("PRAGMA table_info(product_requests)")
        columns = await cursor.fetchall()
        print('Структура таблицы product_requests:')
        for col in columns:
            print(f'  {col[1]} {col[2]} {"NOT NULL" if col[3] else ""} {"PRIMARY KEY" if col[5] else ""}')
        
        # Пробуем вставить запись и посмотреть на ошибку
        try:
            await db.execute('INSERT INTO admins (user_id, is_main, is_limited) VALUES (999999999, 1, 0)')
            await db.commit()
            print('\nТестовая вставка прошла успешно')
            await db.execute('DELETE FROM admins WHERE user_id = 999999999')
            await db.commit()
        except Exception as e:
            print(f'\nОшибка при тестовой вставке: {e}')

if __name__ == "__main__":
    asyncio.run(check_schema()) 