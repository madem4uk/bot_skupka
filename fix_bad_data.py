import asyncio
import aiosqlite
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_and_fix_bad_data():
    """Анализ и исправление проблемных данных"""
    
    try:
        conn = await aiosqlite.connect('database.sqlite')
        
        print("\n=== АНАЛИЗ ПРОБЛЕМНЫХ ДАННЫХ ===\n")
        
        # Анализ product_requests с None значениями
        print("1. АНАЛИЗ ЗАПРОСОВ ТОВАРОВ:")
        cursor = await conn.execute("""
            SELECT id, name, platform, user_id, status, created_at, photo_id, filter, cashback, counts
            FROM product_requests 
            WHERE name = 'None' OR platform = 'None'
            ORDER BY id
        """)
        bad_requests = await cursor.fetchall()
        
        if bad_requests:
            print(f"Найдено {len(bad_requests)} проблемных запросов:")
            for req in bad_requests:
                print(f"  ID: {req[0]}, name: '{req[1]}', platform: '{req[2]}', user_id: {req[3]}")
                print(f"    status: {req[4]}, created_at: {req[5]}, photo_id: {req[6]}")
                print(f"    filter: '{req[7]}', cashback: {req[8]}, counts: '{req[9]}'")
                print()
        else:
            print("  Проблемных запросов не найдено")
        
        # Анализ пустых отзывов
        print("2. АНАЛИЗ ПУСТЫХ ОТЗЫВОВ:")
        cursor = await conn.execute("""
            SELECT f.id, f.text, f.user_id, f.product_id, f.status, f.date, p.keywords
            FROM feedbacks f
            LEFT JOIN products p ON f.product_id = p.id
            WHERE f.text IS NULL OR f.text = ''
        """)
        bad_feedbacks = await cursor.fetchall()
        
        if bad_feedbacks:
            print(f"Найдено {len(bad_feedbacks)} пустых отзывов:")
            for feedback in bad_feedbacks:
                print(f"  ID: {feedback[0]}, text: '{feedback[1]}', user_id: {feedback[2]}")
                print(f"    product_id: {feedback[3]}, status: {feedback[4]}, date: {feedback[5]}")
                print(f"    product_keywords: '{feedback[6]}'")
                print()
        else:
            print("  Пустых отзывов не найдено")
        
        # Проверка связанных данных
        print("3. ПРОВЕРКА СВЯЗАННЫХ ДАННЫХ:")
        
        # Проверяем, есть ли товары для этих отзывов
        cursor = await conn.execute("""
            SELECT DISTINCT f.product_id 
            FROM feedbacks f
            LEFT JOIN products p ON f.product_id = p.id
            WHERE (f.text IS NULL OR f.text = '') AND p.id IS NULL
        """)
        orphan_feedbacks = await cursor.fetchone()
        if orphan_feedbacks:
            print(f"  Найдены отзывы для несуществующих товаров: {orphan_feedbacks[0]}")
        
        # Проверяем статусы запросов
        cursor = await conn.execute("""
            SELECT status, COUNT(*) 
            FROM product_requests 
            WHERE name = 'None' OR platform = 'None'
            GROUP BY status
        """)
        status_counts = await cursor.fetchall()
        print("  Статусы проблемных запросов:")
        for status, count in status_counts:
            status_names = {0: "Ожидание", 1: "Одобрен", 2: "Отклонен"}
            print(f"    {status_names.get(status, status)}: {count}")
        
        print("\n=== ИСПРАВЛЕНИЕ ДАННЫХ ===\n")
        
        # Удаление проблемных запросов
        print("Удаление проблемных запросов товаров...")
        cursor = await conn.execute("""
            DELETE FROM product_requests 
            WHERE name = 'None' OR platform = 'None'
        """)
        deleted_requests = cursor.rowcount
        print(f"Удалено запросов: {deleted_requests}")
        
        # Удаление пустых отзывов
        print("Удаление пустых отзывов...")
        cursor = await conn.execute("""
            DELETE FROM feedbacks 
            WHERE text IS NULL OR text = ''
        """)
        deleted_feedbacks = cursor.rowcount
        print(f"Удалено отзывов: {deleted_feedbacks}")
        
        # Удаление связанных записей
        print("Удаление связанных записей...")
        
        # Удаляем раздачи для несуществующих товаров
        cursor = await conn.execute("""
            DELETE FROM giveaways 
            WHERE product_id NOT IN (SELECT id FROM products)
        """)
        deleted_giveaways = cursor.rowcount
        print(f"Удалено раздач для несуществующих товаров: {deleted_giveaways}")
        
        # Удаляем платежи для несуществующих товаров
        cursor = await conn.execute("""
            DELETE FROM payments 
            WHERE product_id NOT IN (SELECT id FROM products)
        """)
        deleted_payments = cursor.rowcount
        print(f"Удалено платежей для несуществующих товаров: {deleted_payments}")
        
        # Удаляем отзывы для несуществующих товаров
        cursor = await conn.execute("""
            DELETE FROM feedbacks 
            WHERE product_id NOT IN (SELECT id FROM products)
        """)
        deleted_orphan_feedbacks = cursor.rowcount
        print(f"Удалено отзывов для несуществующих товаров: {deleted_orphan_feedbacks}")
        
        await conn.commit()
        
        print(f"\n=== РЕЗУЛЬТАТ ===")
        print(f"Всего удалено записей: {deleted_requests + deleted_feedbacks + deleted_giveaways + deleted_payments + deleted_orphan_feedbacks}")
        
        # Финальная статистика
        print("\n=== ФИНАЛЬНАЯ СТАТИСТИКА ===")
        cursor = await conn.execute("SELECT COUNT(*) FROM products")
        total_products = await cursor.fetchone()
        print(f"Товаров: {total_products[0]}")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM product_requests")
        total_requests = await cursor.fetchone()
        print(f"Запросов: {total_requests[0]}")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM giveaways")
        total_giveaways = await cursor.fetchone()
        print(f"Раздач: {total_giveaways[0]}")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM payments")
        total_payments = await cursor.fetchone()
        print(f"Платежей: {total_payments[0]}")
        
        cursor = await conn.execute("SELECT COUNT(*) FROM feedbacks")
        total_feedbacks = await cursor.fetchone()
        print(f"Отзывов: {total_feedbacks[0]}")
        
    except Exception as e:
        logger.error(f"Ошибка при анализе и исправлении: {e}")
    finally:
        await conn.close()

async def explain_why_bad_data_occurred():
    """Объяснение причин появления проблемных данных"""
    
    print("\n=== ПРИЧИНЫ ПОЯВЛЕНИЯ ПРОБЛЕМНЫХ ДАННЫХ ===\n")
    
    print("1. ЗАПРОСЫ ТОВАРОВ С 'None' ЗНАЧЕНИЯМИ:")
    print("   - Причина: В коде add_product_request_full() не передаются параметры name и platform")
    print("   - Место: handlers/admin.py - функция add_product_request_full")
    print("   - Проблема: Функция вызывается без обязательных параметров")
    print("   - Решение: Добавить проверки и значения по умолчанию")
    print()
    
    print("2. ПУСТЫЕ ОТЗЫВЫ:")
    print("   - Причина: Пользователи отправляют отзывы без текста")
    print("   - Место: handlers/user.py - обработка отзывов")
    print("   - Проблема: Нет валидации на пустой текст")
    print("   - Решение: Добавить проверку на непустой текст перед сохранением")
    print()
    
    print("3. ОРФАННЫЕ ЗАПИСИ:")
    print("   - Причина: Удаление товаров без каскадного удаления связанных записей")
    print("   - Проблема: В базе остаются ссылки на несуществующие товары")
    print("   - Решение: Использовать CASCADE в FOREIGN KEY или ручное удаление")
    print()
    
    print("4. ПРЕДОТВРАЩЕНИЕ В БУДУЩЕМ:")
    print("   - Добавить валидацию данных перед сохранением")
    print("   - Использовать NOT NULL ограничения где это необходимо")
    print("   - Добавить проверки на существование связанных записей")
    print("   - Логировать все операции с базой данных")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "explain":
        asyncio.run(explain_why_bad_data_occurred())
    else:
        print("Выберите действие:")
        print("1. Анализ и исправление данных")
        print("2. Объяснение причин")
        
        choice = input("Введите номер (1-2): ").strip()
        
        if choice == "1":
            confirm = input("Удалить проблемные данные? (да/нет): ").strip().lower()
            if confirm == "да":
                asyncio.run(analyze_and_fix_bad_data())
            else:
                print("Операция отменена")
        elif choice == "2":
            asyncio.run(explain_why_bad_data_occurred())
        else:
            print("Неверный выбор") 