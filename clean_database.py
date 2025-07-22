import asyncio
import aiosqlite
from database import DataBase
from other import get_logger

logger = get_logger(__name__)

async def clean_database():
    """Очистка всей базы данных"""
    db = DataBase('database.sqlite')
    
    try:
        conn = await db.open()
        
        # Список всех таблиц для очистки
        tables = [
            'users',
            'products', 
            'admins',
            'product_requests',
            'feedbacks',
            'giveaways',
            'payments'
        ]
        
        logger.info("Начинаю очистку базы данных...")
        
        # Очищаем каждую таблицу
        for table in tables:
            try:
                await conn.execute(f"DELETE FROM {table}")
                logger.info(f"Очищена таблица: {table}")
            except Exception as e:
                logger.error(f"Ошибка при очистке таблицы {table}: {e}")
        
        # Сбрасываем автоинкрементные счетчики
        await conn.execute("DELETE FROM sqlite_sequence")
        logger.info("Сброшены автоинкрементные счетчики")
        
        await conn.commit()
        logger.info("База данных успешно очищена!")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке базы данных: {e}")
    finally:
        await conn.close()

async def clean_specific_data():
    """Очистка только проблемных данных"""
    db = DataBase('database.sqlite')
    
    try:
        conn = await db.open()
        
        logger.info("Очистка проблемных данных...")
        
        # Удаляем продукты с пустыми ключевыми словами
        await conn.execute("DELETE FROM products WHERE keywords IS NULL OR keywords = '' OR keywords = 'Не указано'")
        logger.info("Удалены продукты с пустыми ключевыми словами")
        
        # Удаляем связанные записи
        await conn.execute("""
            DELETE FROM giveaways WHERE product_id NOT IN (SELECT id FROM products)
        """)
        logger.info("Удалены записи раздач для несуществующих продуктов")
        
        await conn.execute("""
            DELETE FROM payments WHERE product_id NOT IN (SELECT id FROM products)
        """)
        logger.info("Удалены записи платежей для несуществующих продуктов")
        
        await conn.execute("""
            DELETE FROM feedbacks WHERE product_id NOT IN (SELECT id FROM products)
        """)
        logger.info("Удалены записи отзывов для несуществующих продуктов")
        
        # Удаляем пользователей без активности
        await conn.execute("""
            DELETE FROM users WHERE user_id NOT IN (
                SELECT DISTINCT user_id FROM giveaways
                UNION
                SELECT DISTINCT user_id FROM payments
                UNION
                SELECT DISTINCT user_id FROM feedbacks
                UNION
                SELECT DISTINCT user_id FROM product_requests
                UNION
                SELECT DISTINCT user_id FROM admins
            )
        """)
        logger.info("Удалены неактивные пользователи")
        
        await conn.commit()
        logger.info("Проблемные данные очищены!")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке проблемных данных: {e}")
    finally:
        await conn.close()

async def show_database_stats():
    """Показать статистику базы данных"""
    db = DataBase('database.sqlite')
    
    try:
        conn = await db.open()
        
        tables = ['users', 'products', 'admins', 'product_requests', 'feedbacks', 'giveaways', 'payments']
        
        print("\n=== СТАТИСТИКА БАЗЫ ДАННЫХ ===")
        for table in tables:
            cursor = await conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = await cursor.fetchone()
            print(f"{table}: {count[0]} записей")
        
        # Проблемные записи
        cursor = await conn.execute("SELECT COUNT(*) FROM products WHERE keywords IS NULL OR keywords = '' OR keywords = 'Не указано'")
        bad_products = await cursor.fetchone()
        print(f"\nПродукты с пустыми ключевыми словами: {bad_products[0]}")
        
        cursor = await conn.execute("""
            SELECT COUNT(*) FROM giveaways g 
            LEFT JOIN products p ON g.product_id = p.id 
            WHERE p.id IS NULL
        """)
        orphan_giveaways = await cursor.fetchone()
        print(f"Записи раздач без продуктов: {orphan_giveaways[0]}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == "full":
            asyncio.run(clean_database())
        elif action == "partial":
            asyncio.run(clean_specific_data())
        elif action == "stats":
            asyncio.run(show_database_stats())
        else:
            print("Использование:")
            print("python clean_database.py full    - полная очистка")
            print("python clean_database.py partial - очистка проблемных данных")
            print("python clean_database.py stats   - показать статистику")
    else:
        print("Выберите действие:")
        print("1. Полная очистка базы данных")
        print("2. Очистка только проблемных данных")
        print("3. Показать статистику")
        
        choice = input("Введите номер (1-3): ").strip()
        
        if choice == "1":
            confirm = input("ВНИМАНИЕ! Это удалит ВСЕ данные из базы. Продолжить? (да/нет): ").strip().lower()
            if confirm == "да":
                asyncio.run(clean_database())
            else:
                print("Операция отменена")
        elif choice == "2":
            asyncio.run(clean_specific_data())
        elif choice == "3":
            asyncio.run(show_database_stats())
        else:
            print("Неверный выбор") 