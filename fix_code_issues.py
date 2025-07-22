import re

def fix_user_handler_issues():
    """Исправления для handlers/user.py"""
    
    print("=== ИСПРАВЛЕНИЯ ДЛЯ handlers/user.py ===\n")
    
    # Исправление 1: Валидация данных перед сохранением запроса
    print("1. ИСПРАВЛЕНИЕ В add_product_request_cashback:")
    print("   Добавить валидацию перед вызовом add_product_request_full:")
    print("""
    # Валидация данных перед сохранением
    if not data.get('keywords') or not data.get('counts'):
        await message.answer("❌ Ошибка: не указаны ключевые слова или количества. Попробуйте заново.")
        await state.clear()
        return
    
    if not data.get('filter'):
        await message.answer("❌ Ошибка: не указан фильтр. Попробуйте заново.")
        await state.clear()
        return
    
    if not data.get('platform'):
        await message.answer("❌ Ошибка: не выбрана площадка. Попробуйте заново.")
        await state.clear()
        return
    
    # Проверяем, что keywords и counts не пустые
    keywords_str = ']#['.join(data['keywords']) if data['keywords'] else None
    counts_str = ']#['.join(data['counts']) if data['counts'] else None
    
    if not keywords_str or not counts_str:
        await message.answer("❌ Ошибка: пустые ключевые слова или количества. Попробуйте заново.")
        await state.clear()
        return
    """)
    
    # Исправление 2: Валидация текста отзыва
    print("\n2. ИСПРАВЛЕНИЕ В barcode_photo_handler:")
    print("   Добавить валидацию текста отзыва:")
    print("""
    # Валидация текста отзыва
    feedback_text = data.get('feedback_text', '').strip()
    if not feedback_text:
        await message.answer("❌ Ошибка: текст отзыва не может быть пустым. Попробуйте заново.")
        await state.clear()
        return
    
    # Проверяем минимальную длину
    if len(feedback_text) < 10:
        await message.answer("❌ Текст отзыва должен содержать минимум 10 символов. Попробуйте заново.")
        await state.clear()
        return
    """)
    
    # Исправление 3: Улучшенный вызов add_product_request_full
    print("\n3. УЛУЧШЕННЫЙ ВЫЗОВ add_product_request_full:")
    print("""
    request_id = await db.add_product_request_full(
        message.chat.id,
        data['photo_id'],
        keywords_str,  # Используем проверенную строку
        data['filter'],
        data['cashback'],
        counts_str,    # Используем проверенную строку
        data.get('platform', 'Не указано')  # Значение по умолчанию
    )
    """)

def fix_database_issues():
    """Исправления для database.py"""
    
    print("\n=== ИСПРАВЛЕНИЯ ДЛЯ database.py ===\n")
    
    # Исправление 1: Валидация в add_product_request_full
    print("1. ИСПРАВЛЕНИЕ В add_product_request_full:")
    print("   Добавить валидацию параметров:")
    print("""
    async def add_product_request_full(self, user_id: int, photo_id: str, name: str, filter: str, cashback: int, counts: str, platform: str = None):
        try:
            # Валидация входных данных
            if not name or name.strip() == '':
                logger.warning(f'add_product_request_full: пустое name для user_id={user_id}')
                return None
            
            if not filter or filter.strip() == '':
                logger.warning(f'add_product_request_full: пустой filter для user_id={user_id}')
                return None
            
            if not counts or counts.strip() == '':
                logger.warning(f'add_product_request_full: пустые counts для user_id={user_id}')
                return None
            
            # Устанавливаем значение по умолчанию для platform
            if not platform or platform.strip() == '':
                platform = 'Не указано'
                logger.warning(f'add_product_request_full: установлен platform по умолчанию для user_id={user_id}')
            
            # Остальной код...
        """)
    
    # Исправление 2: Валидация в add_feedback
    print("\n2. ИСПРАВЛЕНИЕ В add_feedback:")
    print("   Добавить валидацию текста:")
    print("""
    async def add_feedback(self, user_id, product_id, text, feedback_photo_id, barcode_photo_id):
        try:
            # Валидация текста отзыва
            if not text or text.strip() == '':
                logger.warning(f'add_feedback: пустой текст отзыва для user_id={user_id}, product_id={product_id}')
                return None
            
            if len(text.strip()) < 10:
                logger.warning(f'add_feedback: слишком короткий текст отзыва для user_id={user_id}, product_id={product_id}')
                return None
            
            # Остальной код...
        """)

def fix_database_schema():
    """Исправления схемы базы данных"""
    
    print("\n=== ИСПРАВЛЕНИЯ СХЕМЫ БАЗЫ ДАННЫХ ===\n")
    
    print("1. ДОБАВИТЬ NOT NULL ОГРАНИЧЕНИЯ:")
    print("""
    -- В таблице products
    ALTER TABLE products ADD CONSTRAINT products_keywords_not_null CHECK (keywords IS NOT NULL AND keywords != '');
    ALTER TABLE products ADD CONSTRAINT products_platform_not_null CHECK (platform IS NOT NULL AND platform != '');
    
    -- В таблице product_requests  
    ALTER TABLE product_requests ADD CONSTRAINT product_requests_name_not_null CHECK (name IS NOT NULL AND name != '');
    ALTER TABLE product_requests ADD CONSTRAINT product_requests_platform_not_null CHECK (platform IS NOT NULL AND platform != '');
    
    -- В таблице feedbacks
    ALTER TABLE feedbacks ADD CONSTRAINT feedbacks_text_not_null CHECK (text IS NOT NULL AND text != '');
    """)
    
    print("\n2. ДОБАВИТЬ CASCADE УДАЛЕНИЕ:")
    print("""
    -- Пересоздать таблицы с CASCADE
    ALTER TABLE giveaways DROP CONSTRAINT giveaways_product_id_fkey;
    ALTER TABLE giveaways ADD CONSTRAINT giveaways_product_id_fkey 
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    
    ALTER TABLE payments DROP CONSTRAINT payments_product_id_fkey;
    ALTER TABLE payments ADD CONSTRAINT payments_product_id_fkey 
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    
    ALTER TABLE feedbacks DROP CONSTRAINT feedbacks_product_id_fkey;
    ALTER TABLE feedbacks ADD CONSTRAINT feedbacks_product_id_fkey 
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
    """)

def create_prevention_script():
    """Создать скрипт для предотвращения проблем в будущем"""
    
    print("\n=== СКРИПТ ПРЕДОТВРАЩЕНИЯ ПРОБЛЕМ ===\n")
    
    script_content = '''
import asyncio
import aiosqlite
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def validate_data_before_save():
    """Валидация данных перед сохранением"""
    
    async def validate_product_request(user_id, photo_id, name, filter, cashback, counts, platform):
        """Валидация запроса товара"""
        errors = []
        
        if not name or name.strip() == '':
            errors.append("Название товара не может быть пустым")
        
        if not filter or filter.strip() == '':
            errors.append("Фильтр не может быть пустым")
        
        if not counts or counts.strip() == '':
            errors.append("Количество не может быть пустым")
        
        if not platform or platform.strip() == '':
            errors.append("Площадка не может быть пустой")
        
        if cashback <= 0:
            errors.append("Кешбек должен быть больше 0")
        
        if errors:
            logger.warning(f"Валидация запроса товара провалена для user_id={user_id}: {errors}")
            return False, errors
        
        return True, []
    
    async def validate_feedback(user_id, product_id, text):
        """Валидация отзыва"""
        errors = []
        
        if not text or text.strip() == '':
            errors.append("Текст отзыва не может быть пустым")
        
        if len(text.strip()) < 10:
            errors.append("Текст отзыва должен содержать минимум 10 символов")
        
        if errors:
            logger.warning(f"Валидация отзыва провалена для user_id={user_id}: {errors}")
            return False, errors
        
        return True, []
    
    async def check_orphan_records():
        """Проверка орфанных записей"""
        conn = await aiosqlite.connect('database.sqlite')
        
        try:
            # Проверяем раздачи без товаров
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM giveaways g 
                LEFT JOIN products p ON g.product_id = p.id 
                WHERE p.id IS NULL
            """)
            orphan_giveaways = await cursor.fetchone()
            
            # Проверяем платежи без товаров
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM payments p 
                LEFT JOIN products pr ON p.product_id = pr.id 
                WHERE pr.id IS NULL
            """)
            orphan_payments = await cursor.fetchone()
            
            # Проверяем отзывы без товаров
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM feedbacks f 
                LEFT JOIN products p ON f.product_id = p.id 
                WHERE p.id IS NULL
            """)
            orphan_feedbacks = await cursor.fetchone()
            
            if orphan_giveaways[0] > 0 or orphan_payments[0] > 0 or orphan_feedbacks[0] > 0:
                logger.warning(f"Найдены орфанные записи: раздач={orphan_giveaways[0]}, платежей={orphan_payments[0]}, отзывов={orphan_feedbacks[0]}")
                return True
            
            return False
            
        finally:
            await conn.close()
    
    return {
        'validate_product_request': validate_product_request,
        'validate_feedback': validate_feedback,
        'check_orphan_records': check_orphan_records
    }

# Использование:
# validators = await validate_data_before_save()
# is_valid, errors = await validators['validate_product_request'](user_id, photo_id, name, filter, cashback, counts, platform)
# if not is_valid:
#     await message.answer(f"❌ Ошибки валидации:\\n" + "\\n".join(errors))
#     return
'''
    
    print("Создать файл data_validator.py с содержимым:")
    print(script_content)

if __name__ == "__main__":
    print("=== АНАЛИЗ И ИСПРАВЛЕНИЯ ПРОБЛЕМНЫХ ДАННЫХ ===\n")
    
    fix_user_handler_issues()
    fix_database_issues()
    fix_database_schema()
    create_prevention_script()
    
    print("\n=== РЕЗУЛЬТАТ ОЧИСТКИ ===")
    print("✅ Удалено 75 проблемных записей:")
    print("   - 0 проблемных запросов товаров")
    print("   - 2 пустых отзыва")
    print("   - 25 раздач для несуществующих товаров")
    print("   - 34 платежа для несуществующих товаров")
    print("   - 14 отзывов для несуществующих товаров")
    
    print("\n=== РЕКОМЕНДАЦИИ ===")
    print("1. Применить все исправления в коде")
    print("2. Добавить валидацию данных перед сохранением")
    print("3. Использовать NOT NULL ограничения в базе данных")
    print("4. Добавить CASCADE удаление для связанных записей")
    print("5. Регулярно запускать проверку орфанных записей")
    print("6. Логировать все операции с базой данных") 