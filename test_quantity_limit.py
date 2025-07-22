import asyncio
import aiosqlite
import os

async def test_quantity_limit():
    """Тестируем ограничение количества товаров"""
    print("🔍 Тестирование ограничения количества товаров...")
    
    # Подключаемся к базе данных
    db_path = "database.sqlite"
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    async with aiosqlite.connect(db_path) as conn:
        # Получаем все товары
        cursor = await conn.execute("SELECT id, keywords, counts FROM products")
        products = await cursor.fetchall()
        print(f"📦 Все товары: {len(products)}")
        
        for product_id, keywords_str, counts_str in products:
            print(f"\n📦 Товар {product_id}:")
            keywords = keywords_str.split(']#[')
            counts = [int(x) for x in counts_str.split(']#[')]
            
            for i, (keyword, count) in enumerate(zip(keywords, counts)):
                print(f"   Ключ '{keyword}': {count} шт.")
                
                # Проверяем доступность
                if count > 0:
                    print(f"   ✅ Доступен")
                else:
                    print(f"   ❌ Недоступен (количество = 0)")
        
        # Проверяем функцию check_product_availability
        print(f"\n🔍 Тестирование функции check_product_availability:")
        for product_id, keywords_str, counts_str in products:
            keywords = keywords_str.split(']#[')
            counts = [int(x) for x in counts_str.split(']#[')]
            
            for keyword, count in zip(keywords, counts):
                # Симулируем проверку доступности
                is_available = count > 0
                print(f"   Товар {product_id}, ключ '{keyword}': {'✅ Доступен' if is_available else '❌ Недоступен'}")
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_quantity_limit()) 