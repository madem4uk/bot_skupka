import asyncio
import aiosqlite
from pathlib import Path

async def clean_orphans():
    db_path = Path(__file__).parent / "database.sqlite"
    if not db_path.exists():
        print("База данных не найдена")
        return
        
    async with aiosqlite.connect(db_path) as conn:
        print("=== ОЧИСТКА БАЗЫ ДАННЫХ ===")
        
        # Проверяем раздачи с несуществующими товарами
        cursor = await conn.execute("""
            SELECT COUNT(*) 
            FROM giveaways g 
            LEFT JOIN products p ON g.product_id = p.id 
            WHERE p.id IS NULL
        """)
        orphan_giveaways_count = (await cursor.fetchone())[0]
        
        # Проверяем отзывы с несуществующими товарами
        cursor = await conn.execute("""
            SELECT COUNT(*) 
            FROM feedbacks f 
            LEFT JOIN products p ON f.product_id = p.id 
            WHERE p.id IS NULL
        """)
        orphan_feedbacks_count = (await cursor.fetchone())[0]
        
        print(f"Найдено раздач с несуществующими товарами: {orphan_giveaways_count}")
        print(f"Найдено отзывов с несуществующими товарами: {orphan_feedbacks_count}")
        
        if orphan_giveaways_count == 0 and orphan_feedbacks_count == 0:
            print("Очистка не требуется - все записи корректны")
            return
        
        # Удаляем раздачи с несуществующими товарами
        if orphan_giveaways_count > 0:
            await conn.execute("""
                DELETE FROM giveaways 
                WHERE product_id NOT IN (SELECT id FROM products)
            """)
            print(f"✅ Удалено {orphan_giveaways_count} раздач с несуществующими товарами")
        
        # Удаляем отзывы с несуществующими товарами
        if orphan_feedbacks_count > 0:
            await conn.execute("""
                DELETE FROM feedbacks 
                WHERE product_id NOT IN (SELECT id FROM products)
            """)
            print(f"✅ Удалено {orphan_feedbacks_count} отзывов с несуществующими товарами")
        
        # Сохраняем изменения
        await conn.commit()
        
        print("\n=== ПРОВЕРКА ПОСЛЕ ОЧИСТКИ ===")
        
        # Проверяем, что все очищено
        cursor = await conn.execute("""
            SELECT COUNT(*) 
            FROM giveaways g 
            LEFT JOIN products p ON g.product_id = p.id 
            WHERE p.id IS NULL
        """)
        remaining_giveaways = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) 
            FROM feedbacks f 
            LEFT JOIN products p ON f.product_id = p.id 
            WHERE p.id IS NULL
        """)
        remaining_feedbacks = (await cursor.fetchone())[0]
        
        print(f"Осталось раздач с несуществующими товарами: {remaining_giveaways}")
        print(f"Осталось отзывов с несуществующими товарами: {remaining_feedbacks}")
        
        if remaining_giveaways == 0 and remaining_feedbacks == 0:
            print("✅ Очистка завершена успешно!")
        else:
            print("⚠️ Некоторые записи остались - возможно, есть проблемы с базой")

if __name__ == "__main__":
    asyncio.run(clean_orphans()) 