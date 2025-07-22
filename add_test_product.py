import asyncio
import aiosqlite
import os

async def add_test_product():
    """Добавляем тестовый товар с количеством больше 0"""
    print("🔧 Добавление тестового товара...")
    
    # Подключаемся к базе данных
    db_path = "database.sqlite"
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    async with aiosqlite.connect(db_path) as conn:
        # Добавляем тестовый товар
        test_photo_id = "test_photo_id"
        test_keywords = "Тестовый товар"
        test_counts = "5"  # 5 штук
        test_filter = "test"
        test_cashback = 100
        test_admin_id = 6696364473  # ID ограниченного админа
        
        try:
            await conn.execute("""
                INSERT INTO products (photo_id, keywords, counts, filter, cashback, admin_id) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (test_photo_id, test_keywords, test_counts, test_filter, test_cashback, test_admin_id))
            await conn.commit()
            print("✅ Тестовый товар добавлен!")
            
            # Проверяем добавление
            cursor = await conn.execute("SELECT id, keywords, counts FROM products ORDER BY id DESC LIMIT 1")
            product = await cursor.fetchone()
            if product:
                print(f"📦 Добавлен товар ID: {product[0]}")
                print(f"   Ключевые слова: {product[1]}")
                print(f"   Количество: {product[2]}")
        except Exception as e:
            print(f"❌ Ошибка при добавлении товара: {e}")

if __name__ == "__main__":
    asyncio.run(add_test_product()) 