import asyncio
import aiosqlite
import os

async def test_feedback_products():
    """Тестируем получение товаров для отзывов"""
    print("🔍 Тестирование товаров для отзывов...")
    
    # Подключаемся к базе данных
    db_path = "database.sqlite"
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    async with aiosqlite.connect(db_path) as conn:
        # Получаем всех пользователей
        cursor = await conn.execute("SELECT user_id FROM users")
        users = [row[0] for row in await cursor.fetchall()]
        print(f"👥 Все пользователи: {users}")
        
        # Получаем все раздачи
        cursor = await conn.execute("SELECT user_id, product_id FROM giveaways")
        giveaways = await cursor.fetchall()
        print(f"🎁 Все раздачи: {giveaways}")
        
        # Получаем все отзывы
        cursor = await conn.execute("SELECT user_id, product_id FROM feedbacks")
        feedbacks = await cursor.fetchall()
        print(f"📝 Все отзывы: {feedbacks}")
        
        # Получаем все товары
        cursor = await conn.execute("SELECT id, keywords, counts FROM products")
        products = await cursor.fetchall()
        print(f"📦 Все товары: {len(products)}")
        
        # Тестируем для каждого пользователя
        for user_id in users:
            print(f"\n👤 Пользователь {user_id}:")
            
            # Товары, в которых участвует в раздаче
            cursor = await conn.execute("SELECT product_id FROM giveaways WHERE user_id = ?", (user_id,))
            giveaway_products = [row[0] for row in await cursor.fetchall()]
            print(f"   🎁 Участвует в раздачах товаров: {giveaway_products}")
            
            # Товары, по которым уже оставил отзыв
            cursor = await conn.execute("SELECT product_id FROM feedbacks WHERE user_id = ?", (user_id,))
            feedback_products = [row[0] for row in await cursor.fetchall()]
            print(f"   📝 Уже оставил отзывы по товарам: {feedback_products}")
            
            # Товары для отзывов (участвует, но не оставлял отзыв)
            products_for_feedback = [p for p in giveaway_products if p not in feedback_products]
            print(f"   ✅ Может оставить отзыв по товарам: {products_for_feedback}")
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_feedback_products()) 