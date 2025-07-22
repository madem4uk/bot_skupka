import asyncio
import aiosqlite
from pathlib import Path

async def check_user():
    db_path = Path(__file__).parent / "database.sqlite"
    if not db_path.exists():
        print("База данных не найдена")
        return
        
    user_id = 5524446848  # ID пользователя из логов
        
    async with aiosqlite.connect(db_path) as conn:
        print(f"=== ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ {user_id} ===")
        
        # Проверяем все раздачи пользователя
        cursor = await conn.execute("""
            SELECT g.id, g.product_id, p.keywords 
            FROM giveaways g 
            LEFT JOIN products p ON g.product_id = p.id 
            WHERE g.user_id = ?
        """, (user_id,))
        giveaways = await cursor.fetchall()
        
        print(f"Всего раздач у пользователя: {len(giveaways)}")
        for giveaway in giveaways:
            giveaway_id, product_id, keywords = giveaway
            if keywords:
                first_keyword = keywords.split(']#[')[0] if ']#[' in keywords else keywords
                print(f"  Раздача {giveaway_id}: product_id={product_id}, товар='{first_keyword}'")
            else:
                print(f"  Раздача {giveaway_id}: product_id={product_id}, товар='Не указано'")
        
        # Проверяем отзывы пользователя
        cursor = await conn.execute("""
            SELECT f.id, f.product_id, f.status, p.keywords 
            FROM feedbacks f 
            LEFT JOIN products p ON f.product_id = p.id 
            WHERE f.user_id = ?
        """, (user_id,))
        feedbacks = await cursor.fetchall()
        
        print(f"\nВсего отзывов у пользователя: {len(feedbacks)}")
        for feedback in feedbacks:
            feedback_id, product_id, status, keywords = feedback
            if keywords:
                first_keyword = keywords.split(']#[')[0] if ']#[' in keywords else keywords
                print(f"  Отзыв {feedback_id}: product_id={product_id}, статус={status}, товар='{first_keyword}'")
            else:
                print(f"  Отзыв {feedback_id}: product_id={product_id}, статус={status}, товар='Не указано'")
        
        # Проверяем активные раздачи (без оплат или с отклоненными оплатами)
        cursor = await conn.execute("""
            SELECT g.id, g.product_id, p.keywords 
            FROM giveaways g
            LEFT JOIN products p ON g.product_id = p.id
            LEFT JOIN payments pay ON g.user_id = pay.user_id AND g.product_id = pay.product_id
            WHERE g.user_id = ? 
            AND g.product_id IN (SELECT id FROM products)
            AND (pay.user_id IS NULL OR pay.status = 2)
        """, (user_id,))
        active_giveaways = await cursor.fetchall()
        
        print(f"\nАктивных раздач (для получения кешбека): {len(active_giveaways)}")
        for giveaway in active_giveaways:
            giveaway_id, product_id, keywords = giveaway
            if keywords:
                first_keyword = keywords.split(']#[')[0] if ']#[' in keywords else keywords
                print(f"  Активная раздача {giveaway_id}: product_id={product_id}, товар='{first_keyword}'")
            else:
                print(f"  Активная раздача {giveaway_id}: product_id={product_id}, товар='Не указано'")

if __name__ == "__main__":
    asyncio.run(check_user()) 