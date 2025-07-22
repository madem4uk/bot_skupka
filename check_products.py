import asyncio
import aiosqlite
import os
from pathlib import Path

async def check_products():
    db_path = Path(__file__).parent / "database.sqlite"
    if not db_path.exists():
        print("База данных не найдена")
        return
        
    async with aiosqlite.connect(db_path) as conn:
        # Удаляем товары с невалидным photo_id
        await conn.execute("DELETE FROM products WHERE photo_id NOT LIKE 'AgAC%' AND photo_id NOT LIKE 'CQAC%' AND photo_id NOT LIKE 'BAAC%' AND photo_id NOT LIKE 'AAAC%'")
        await conn.commit()
        print("✅ Удалены товары с невалидным photo_id")
        # Проверяем таблицу products
        print("=== ТАБЛИЦА PRODUCTS ===")
        cursor = await conn.execute("SELECT id, keywords, cashback FROM products")
        products = await cursor.fetchall()
        
        print(f'Найдено товаров: {len(products)}')
        print('---')
        
        for product in products:
            product_id, keywords, cashback = product
            if keywords:
                first_keyword = keywords.split(']#[')[0] if ']#[' in keywords else keywords
                print(f'Товар {product_id}: {first_keyword}')
                print(f'  Кешбек: {cashback}₽')
            else:
                print(f'Товар {product_id}: keywords = "{keywords}" (пустое)')
                print(f'  Кешбек: {cashback}₽')
            print('---')
        
        # Проверяем таблицу giveaways
        print("\n=== ТАБЛИЦА GIVEAWAYS ===")
        cursor = await conn.execute("SELECT id, user_id, product_id FROM giveaways")
        giveaways = await cursor.fetchall()
        print(f'Найдено раздач: {len(giveaways)}')
        
        for giveaway in giveaways:
            giveaway_id, user_id, product_id = giveaway
            print(f'Раздача {giveaway_id}: user_id={user_id}, product_id={product_id}')
        
        # Проверяем таблицу feedbacks
        print("\n=== ТАБЛИЦА FEEDBACKS ===")
        cursor = await conn.execute("SELECT id, user_id, product_id, status FROM feedbacks")
        feedbacks = await cursor.fetchall()
        print(f'Найдено отзывов: {len(feedbacks)}')
        
        for feedback in feedbacks:
            feedback_id, user_id, product_id, status = feedback
            print(f'Отзыв {feedback_id}: user_id={user_id}, product_id={product_id}, status={status}')
        
        # Проверяем, есть ли раздачи/отзывы с несуществующими товарами
        print("\n=== ПРОВЕРКА НЕСУЩЕСТВУЮЩИХ ТОВАРОВ ===")
        cursor = await conn.execute("""
            SELECT DISTINCT g.product_id 
            FROM giveaways g 
            LEFT JOIN products p ON g.product_id = p.id 
            WHERE p.id IS NULL
        """)
        orphan_giveaways = await cursor.fetchall()
        print(f'Раздачи с несуществующими товарами: {len(orphan_giveaways)}')
        for orphan in orphan_giveaways:
            print(f'  product_id: {orphan[0]}')
        
        cursor = await conn.execute("""
            SELECT DISTINCT f.product_id 
            FROM feedbacks f 
            LEFT JOIN products p ON f.product_id = p.id 
            WHERE p.id IS NULL
        """)
        orphan_feedbacks = await cursor.fetchall()
        print(f'Отзывы с несуществующими товарами: {len(orphan_feedbacks)}')
        for orphan in orphan_feedbacks:
            print(f'  product_id: {orphan[0]}')

        # Удаляем раздачи с несуществующими товарами
        await conn.execute("DELETE FROM giveaways WHERE product_id NOT IN (SELECT id FROM products)")
        await conn.commit()
        print("✅ Удалены раздачи с несуществующими товарами")
        # Удаляем отзывы с несуществующими товарами
        await conn.execute("DELETE FROM feedbacks WHERE product_id NOT IN (SELECT id FROM products)")
        await conn.commit()
        print("✅ Удалены отзывы с несуществующими товарами")

if __name__ == "__main__":
    asyncio.run(check_products()) 