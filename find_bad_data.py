import asyncio
import aiosqlite
from database import DataBase
from other import get_logger

logger = get_logger(__name__)

async def find_bad_data():
    """Найти все записи с 'Не указано' в базе данных"""
    db = DataBase('database.sqlite')
    
    try:
        conn = await db.open()
        
        print("\n=== ПОИСК ЗАПИСЕЙ С 'НЕ УКАЗАНО' ===\n")
        
        # Поиск в таблице products
        print("1. ТОВАРЫ (products):")
        cursor = await conn.execute("""
            SELECT id, keywords, platform, admin_id 
            FROM products 
            WHERE keywords LIKE '%Не указано%' 
            OR platform LIKE '%Не указано%'
            OR keywords IS NULL 
            OR keywords = ''
        """)
        products = await cursor.fetchall()
        
        if products:
            for product in products:
                print(f"  ID: {product[0]}, keywords: '{product[1]}', platform: '{product[2]}', admin_id: {product[3]}")
        else:
            print("  Не найдено")
        
        # Поиск в таблице product_requests
        print("\n2. ЗАПРОСЫ ТОВАРОВ (product_requests):")
        cursor = await conn.execute("""
            SELECT id, name, platform, user_id 
            FROM product_requests 
            WHERE name LIKE '%Не указано%' 
            OR platform LIKE '%Не указано%'
            OR name IS NULL 
            OR name = ''
        """)
        requests = await cursor.fetchall()
        
        if requests:
            for req in requests:
                print(f"  ID: {req[0]}, name: '{req[1]}', platform: '{req[2]}', user_id: {req[3]}")
        else:
            print("  Не найдено")
        
        # Поиск в таблице feedbacks
        print("\n3. ОТЗЫВЫ (feedbacks):")
        cursor = await conn.execute("""
            SELECT id, text, user_id, product_id 
            FROM feedbacks 
            WHERE text LIKE '%Не указано%'
            OR text IS NULL 
            OR text = ''
        """)
        feedbacks = await cursor.fetchall()
        
        if feedbacks:
            for feedback in feedbacks:
                print(f"  ID: {feedback[0]}, text: '{feedback[1][:50]}...', user_id: {feedback[2]}, product_id: {feedback[3]}")
        else:
            print("  Не найдено")
        
        # Поиск в таблице payments
        print("\n4. ПЛАТЕЖИ (payments):")
        cursor = await conn.execute("""
            SELECT id, details, user_id, product_id 
            FROM payments 
            WHERE details LIKE '%Не указано%'
            OR details IS NULL 
            OR details = ''
        """)
        payments = await cursor.fetchall()
        
        if payments:
            for payment in payments:
                print(f"  ID: {payment[0]}, details: '{payment[1][:50]}...', user_id: {payment[2]}, product_id: {payment[3]}")
        else:
            print("  Не найдено")
        
        # Общая статистика
        print("\n=== ОБЩАЯ СТАТИСТИКА ===")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM products WHERE keywords LIKE '%Не указано%' OR keywords IS NULL OR keywords = ''")
        bad_products = await cursor.fetchone()
        print(f"Товары с проблемными keywords: {bad_products[0]}")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM product_requests WHERE name LIKE '%Не указано%' OR name IS NULL OR name = ''")
        bad_requests = await cursor.fetchone()
        print(f"Запросы с проблемными name: {bad_requests[0]}")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM products WHERE platform LIKE '%Не указано%' OR platform IS NULL")
        bad_platforms = await cursor.fetchone()
        print(f"Товары с проблемными platform: {bad_platforms[0]}")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM product_requests WHERE platform LIKE '%Не указано%' OR platform IS NULL")
        bad_request_platforms = await cursor.fetchone()
        print(f"Запросы с проблемными platform: {bad_request_platforms[0]}")
        
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(find_bad_data()) 