import asyncio
import aiosqlite
import os

async def test_payments_filtering():
    """Тестируем фильтрацию оплат по админам"""
    print("🔍 Тестирование фильтрации оплат по админам...")
    
    # Подключаемся к базе данных
    db_path = "database.sqlite"
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    async with aiosqlite.connect(db_path) as conn:
        # Получаем всех админов
        cursor = await conn.execute("SELECT user_id, is_main, is_limited FROM admins")
        admins = await cursor.fetchall()
        print(f"📋 Все админы: {admins}")
        
        # Проверяем главного админа
        main_admin = None
        limited_admins = []
        for admin_id, is_main, is_limited in admins:
            if is_main:
                main_admin = admin_id
            if is_limited:
                limited_admins.append(admin_id)
        
        print(f"👑 Главный админ: {main_admin}")
        print(f"🔒 Ограниченные админы: {limited_admins}")
        
        # Получаем все оплаты
        cursor = await conn.execute("SELECT id FROM payments WHERE STATUS = 0")
        all_payments = [row[0] for row in await cursor.fetchall()]
        print(f"💳 Все оплаты: {len(all_payments)}")
        
        # Тестируем получение оплат для главного админа
        if main_admin:
            cursor = await conn.execute("""
                SELECT p.id FROM payments p 
                JOIN products pr ON p.product_id = pr.id 
                WHERE p.STATUS = 0 AND pr.admin_id = ?
            """, (main_admin,))
            main_admin_payments = [row[0] for row in await cursor.fetchall()]
            print(f"💳 Оплаты главного админа: {len(main_admin_payments)}")
            print(f"✅ Главный админ видит все оплаты: {len(all_payments) == len(main_admin_payments)}")
        
        # Тестируем получение оплат для ограниченных админов
        for admin_id in limited_admins:
            cursor = await conn.execute("""
                SELECT p.id FROM payments p 
                JOIN products pr ON p.product_id = pr.id 
                WHERE p.STATUS = 0 AND pr.admin_id = ?
            """, (admin_id,))
            admin_payments = [row[0] for row in await cursor.fetchall()]
            print(f"💳 Оплаты админа {admin_id}: {len(admin_payments)}")
            
            if admin_payments:
                print(f"   📦 ID оплат: {admin_payments}")
        
        # Проверяем товары и их админов
        cursor = await conn.execute("SELECT id, admin_id FROM products")
        products = await cursor.fetchall()
        print(f"📦 Все товары: {len(products)}")
        for product_id, admin_id in products:
            print(f"   Товар {product_id}: админ {admin_id}")
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_payments_filtering()) 