import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from database import db

async def test_payments_filtering():
    """Тестируем фильтрацию оплат по админам"""
    print("🔍 Тестирование фильтрации оплат по админам...")
    
    # Инициализируем базу данных
    await db.create_tables()
    
    # Получаем всех админов
    admins = await db.get_admins()
    print(f"📋 Все админы: {admins}")
    
    # Проверяем главного админа
    main_admin = None
    for admin_id in admins:
        if await db.check_is_main_admin(admin_id):
            main_admin = admin_id
            break
    
    print(f"👑 Главный админ: {main_admin}")
    
    # Тестируем получение оплат для главного админа (должны быть все)
    if main_admin:
        all_payments = await db.get_payments()
        main_admin_payments = await db.get_payments(main_admin)
        print(f"💳 Все оплаты: {len(all_payments)}")
        print(f"💳 Оплаты главного админа: {len(main_admin_payments)}")
        print(f"✅ Главный админ видит все оплаты: {len(all_payments) == len(main_admin_payments)}")
    
    # Тестируем получение оплат для ограниченных админов
    limited_admins = []
    for admin_id in admins:
        if await db.check_is_limited_admin(admin_id):
            limited_admins.append(admin_id)
    
    print(f"🔒 Ограниченные админы: {limited_admins}")
    
    for admin_id in limited_admins:
        admin_payments = await db.get_payments(admin_id)
        print(f"💳 Оплаты админа {admin_id}: {len(admin_payments)}")
        
        # Проверяем, что админ видит только оплаты по своим товарам
        if admin_payments:
            print(f"   📦 ID оплат: {admin_payments}")
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_payments_filtering()) 