import asyncio
import aiosqlite

async def delete_test_product():
    async with aiosqlite.connect('database.sqlite') as conn:
        await conn.execute('DELETE FROM products WHERE id = 17')
        await conn.commit()
        print('✅ Тестовый товар удалён!')

if __name__ == '__main__':
    asyncio.run(delete_test_product()) 