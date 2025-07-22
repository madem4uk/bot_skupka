import asyncio
import aiosqlite

async def print_all_products_keywords():
    async with aiosqlite.connect('database.sqlite') as db:
        cursor = await db.execute("SELECT id, keywords, counts FROM products")
        rows = await cursor.fetchall()
        if not rows:
            print("В базе нет товаров")
            return
        for row in rows:
            product_id = row[0]
            keywords = row[1].split(']#[') if row[1] else []
            counts = row[2].split(']#[') if row[2] else []
            print(f"Товар id={product_id}")
            for k, c in zip(keywords, counts):
                print(f"  '{k}': {c}")
            print()

if __name__ == "__main__":
    asyncio.run(print_all_products_keywords()) 