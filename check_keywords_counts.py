import asyncio
import aiosqlite

async def print_keywords_counts(product_id):
    async with aiosqlite.connect('database.sqlite') as db:
        cursor = await db.execute("SELECT keywords, counts FROM products WHERE id = ?", (product_id,))
        row = await cursor.fetchone()
        if not row:
            print(f"Товар с id={product_id} не найден")
            return
        keywords = row[0].split(']#[') if row[0] else []
        counts = row[1].split(']#[') if row[1] else []
        print(f"Товар id={product_id}")
        for k, c in zip(keywords, counts):
            print(f"  '{k}': {c}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Использование: python check_keywords_counts.py <product_id>")
    else:
        asyncio.run(print_keywords_counts(int(sys.argv[1]))) 