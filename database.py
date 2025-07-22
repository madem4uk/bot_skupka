import aiosqlite
from os import getenv, path
from other import get_logger
from datetime import datetime
from random import choice


logger = get_logger(__name__)


class DataBase:
    def __init__(self, filename):
        self._filename = filename
        
    def random_split_text(self, text):
        prompt = ']#['
        if isinstance(text, (list, tuple)):
            if not text:
                return '...'
            text = text[0]
        if not isinstance(text, str):
            return '...'
        if prompt in text:
            if text:
                return choice(text.split(prompt))
            else:
                return '...'
        if text.strip():
            return text
        return '...'

    async def create_tables(self):
        """Создание таблиц"""
        try:
            conn = await self.open()
            await conn.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER NOT NULL PRIMARY KEY
            )""")

            await conn.execute("""CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_id TEXT NOT NULL,
                keywords TEXT NOT NULL,
                counts TEXT NOT NULL,
                filter TEXT NOT NULL,
                cashback INTEGER NOT NULL,
                admin_id INTEGER,
                platform TEXT, -- новое поле для площадки
                FOREIGN KEY (admin_id) REFERENCES admins(user_id) ON DELETE SET NULL
            )""")
            # Миграция для старых баз: добавляем platform, если его нет
            try:
                await conn.execute("ALTER TABLE products ADD COLUMN platform TEXT")
            except Exception:
                pass

            await conn.execute("""CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER NOT NULL PRIMARY KEY,
                is_main INTEGER CHECK (is_main IN (0, 1)),
                is_limited INTEGER CHECK (is_limited IN (0, 1)) DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""")

            # Добавляем platform
            await conn.execute("""CREATE TABLE IF NOT EXISTS product_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                payment_photo_id TEXT NOT NULL,
                status INTEGER CHECK (status IN (0, 1, 2)) DEFAULT 0,
                created_at TEXT NOT NULL,
                name TEXT,
                filter TEXT,
                cashback INTEGER,
                counts TEXT,
                photo_id TEXT, -- новое поле для file_id фото товара
                platform TEXT, -- новое поле для площадки
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""")
            # Миграция для старых баз
            try:
                await conn.execute("ALTER TABLE product_requests ADD COLUMN platform TEXT")
            except Exception:
                pass

            # status = 0 - Ожидание; status = 1 - Одобрён; status = 2 - Отклонён
            await conn.execute("""CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                feedback_photo_id TEXT NOT NULL,
                barcode_photo_id TEXT NOT NULL,
                status INTEGER CHECK (status IN (0, 1, 2)) DEFAULT 0,
                date TEXT NOT NULL,
                UNIQUE (user_id, product_id),
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )""")

            await conn.execute("""CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                keyword TEXT NOT NULL, -- Добавляем поле keyword
                UNIQUE (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )""")
            
            # status = 0 - Ожидание; status = 1 - Одобрён; status = 2 - Отклонён
            await conn.execute("""CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                details TEXT NOT NULL,
                photo_id TEXT NOT NULL,
                status INTEGER CHECK (status IN (0, 1, 2)) DEFAULT 0,
                UNIQUE (user_id, product_id, status),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )""")
            await conn.commit()
            logger.info('Таблицы созданы')
            await conn.execute("""CREATE TABLE IF NOT EXISTS payment_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                requisites TEXT NOT NULL DEFAULT '+3242424',
                amount INTEGER NOT NULL DEFAULT 0,
                is_free_mode INTEGER NOT NULL DEFAULT 0
            )""")
            # Гарантируем одну строку по умолчанию
            await conn.execute("INSERT OR IGNORE INTO payment_settings (id, requisites, amount, is_free_mode) VALUES (1, '+3242424', 0, 0)")
            await conn.commit()
            logger.info('Таблицы созданы')
        except Exception as e:
            logger.warning(f'Ошибка при создании таблиц - {e}')
            
    async def del_giveaway(self, giveaway_id):
        """Удаление участия в раздаче"""
        try:
            logger.info(f'Удаление участия в раздаче')  
            conn = await self.open()
            await conn.execute("""DELETE FROM giveaways WHERE id = ?""", (giveaway_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при удалении участия в раздаче - {e}')
            
    async def set_payment_status(self, payment_id, status: int):
        """Изменение статуса платежа"""
        try:
            logger.info(f'Изменение статуса платежа')  
            conn = await self.open()
            await conn.execute("""UPDATE payments SET status = ? WHERE id = ?""", (status if status in [1, 2] else 0, payment_id))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при изменение статуса платежа - {e}') 
            
    async def get_payment(self, payment_id):
        """Получение данных о выплате"""
        try:
            logger.info('Получение данных о выплате')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT * FROM payments WHERE id = ?""", (payment_id,))
            data = await cursor.fetchone()
            if data:
                cursor = await conn.execute("""SELECT cashback FROM products WHERE id = ?""", (data[2],))
                data1 = await cursor.fetchone()
                if data1:
                    return {'user_id': data[1], 'product_id': data[2], 'details': data[3], 'photo_id': data[4], 'cashback': data1[0]}
            return {}
        except Exception as e:
            logger.warning(f'Ошибка при получении данных о выплате - {e}')   
            
    async def get_active_giveaways(self, user_id):
        """Получение активных раздач пользователя"""
        try:
            logger.info('Получение активных раздач пользователя')  
            conn = await self.open()
            cursor = await conn.execute("""
SELECT g.id FROM giveaways g
LEFT JOIN payments p 
    ON g.user_id = p.user_id 
    AND g.product_id = p.product_id
WHERE 
    g.user_id = ? 
    AND g.product_id IN (SELECT id FROM products)
    AND (
        p.user_id IS NULL 
        OR p.status = 2
    )
    AND g.product_id NOT IN (
        SELECT product_id FROM payments WHERE user_id = g.user_id AND status = 1
    )
""", (user_id,))
            return [a[0] for a in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении активных раздач пользователя - {e}')
            return []
            
    async def get_giveaway_name(self, giveaway_id):
        """Получение имени раздачи по id"""
        try:
            logger.info('Получение имени раздачи по id')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT p.keywords FROM giveaways g JOIN products p ON g.product_id = p.id WHERE g.id = ?""", (giveaway_id,))
            keywords = await cursor.fetchone()
            if keywords and keywords[0]:
                return self.random_split_text(keywords[0])
            else:
                return "Не указано"
        except Exception as e:
            logger.warning(f'Ошибка при получении имени раздачи по id - {e}')
            return "Не указано"
            
    async def get_product_with_giveaway(self, giveaway_id):
        """Получение product_id по giveaway_id"""
        try:
            logger.info('Получение имени раздачи по id')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT product_id FROM giveaways WHERE id = ?""", (giveaway_id,))
            result = await cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.warning(f'Ошибка при получении имени раздачи по id - {e}')
            
    async def get_payment_data(self, payment_id):
        """Получение данных о выплате ([user_id, product_id])"""
        try:
            logger.info('Получение данных о выплате')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id, product_id FROM payments WHERE id = ?""", (payment_id,))
            data1 = await cursor.fetchone()
            if data1:
                cursor = await conn.execute("""SELECT cashback FROM products WHERE id = ?""", (data1[1],))
                data2 = await cursor.fetchone()
                if data2:
                    return [data1[0], data2[0]]
            return []
        except Exception as e:
            logger.warning(f'Ошибка при получении данных о выплате - {e}')   
            
    async def get_payments(self, admin_id: int = None):
        """Получение заявок оплат"""
        try:
            logger.info('Получение заявок на оплаты')  
            conn = await self.open()
            if admin_id:
                # Получаем оплаты только по товарам этого админа
                cursor = await conn.execute("""
                    SELECT p.id FROM payments p 
                    JOIN products pr ON p.product_id = pr.id 
                    WHERE p.STATUS = 0 AND pr.admin_id = ?
                """, (admin_id,))
            else:
                # Получаем все оплаты (для главного админа)
                cursor = await conn.execute("""SELECT id FROM payments WHERE STATUS = 0""")
            return [a[0] for a in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении заявок на оплаты - {e}')   
            
    async def del_payments(self, payment_id):
        """Удаление заявки оплаты"""
        try:
            logger.info(f'Удаление заявки оплаты')  
            conn = await self.open()
            await conn.execute("""DELETE FROM payments WHERE id = ?""", (payment_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при удалении заявки оплаты - {e}')
            
    async def add_payment(self, user_id, product_id, details, photo_id):
        """Добавление заявки оплаты"""
        try:
            logger.info(f'Добавление заявки оплаты')  
            conn = await self.open()
            await conn.execute("""INSERT OR IGNORE INTO payments (user_id, product_id, details, photo_id) VALUES (?, ?, ?, ?)""", (user_id, product_id, details, photo_id))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при добавлении заявки оплаты - {e}')
            
    async def get_user_from_feedback(self, feedback_id):
        """Получение пользователя из отзыва"""
        try:
            logger.info('Получение пользователя из отзыва')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id FROM feedbacks WHERE id = ?""", (feedback_id,))
            user = await cursor.fetchone()
            return user[0] if user else None
        except Exception as e:
            logger.warning(f'Ошибка при получении пользователя из отзыва - {e}')
            
    async def check_giveaway(self, user_id: int, product_id: int):
        """Проверка на участие в раздаче"""
        try:
            logger.info(f'Проверка на участие в раздаче')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT id FROM giveaways WHERE user_id = ? AND product_id = ?""", (user_id, product_id))
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f'Ошибка при проверке на участие в раздаче - {e}')  
            
    async def set_feedbacks_status(self, feedback_id, status: int):
        """Изменение статуса участия в отзыве"""
        try:
            logger.info(f'Изменение статуса участия в отзыве')  
            conn = await self.open()
            await conn.execute("""UPDATE feedbacks SET status = ? WHERE id = ?""", (status if status in [1, 2] else 0, feedback_id))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при изменение статуса участия в отзыве - {e}') 
            
    async def get_feedback_status(self, user_id: int, product_id: int):
        """Получение статуса отзыва пользователя по товару"""
        try:
            logger.info(f'Получение статуса отзыва пользователя {user_id} по товару {product_id}')
            conn = await self.open()
            cursor = await conn.execute("""SELECT status FROM feedbacks WHERE user_id = ? AND product_id = ?""", (user_id, product_id))
            result = await cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.warning(f'Ошибка при получении статуса отзыва - {e}')
            return None 
            
    async def check_product_availability(self, product_id, keyword):
        """Проверка доступности товара по ключевому слову"""
        try:
            logger.info(f'Проверка доступности товара {product_id} по ключевому слову {keyword}')
            data = await self.get_product_keywords(product_id)
            for keyword_data, count in data:
                if keyword_data == keyword and count > 0:
                    return True
            return False
        except Exception as e:
            logger.warning(f'Ошибка при проверке доступности товара - {e}')
            return False
            
    async def add_giveaway(self, user_id, product_id, keyword):
        """Добавление участия в раздаче"""
        try:
            logger.info(f'Добавление участия в раздаче')  
            # Проверяем доступность товара
            if not await self.check_product_availability(product_id, keyword):
                logger.warning(f'Товар {product_id} недоступен по ключевому слову {keyword}')
                return False
                
            data = await self.get_product_keywords(product_id)
            conn = await self.open()
            await conn.execute("""INSERT OR IGNORE INTO giveaways (user_id, product_id, keyword) VALUES (?, ?, ?)""", (user_id, product_id, keyword))
            await conn.commit()
            result = []
            for d in data:
                if d[0] == keyword:
                    result.append([d[0], d[1] - 1])
                else:
                    result.append(d)
            await self._update_keywords_and_counts(product_id, result)
            return True
        except Exception as e:
            logger.warning(f'Ошибка при добавлении участия в раздаче - {e}') 
            return False 
    
    async def add_feedback(self, user_id, product_id, text, feedback_photo_id, barcode_photo_id):
        """Добавление отзыва"""
        try:
            logger.info(f'Добавление отзыва')  
            conn = await self.open()
            cursor = await conn.execute("""INSERT OR IGNORE INTO feedbacks (user_id, product_id, text, feedback_photo_id, barcode_photo_id, date) VALUES (?, ?, ?, ?, ?, ?)""", 
                                        (user_id, product_id, text, feedback_photo_id, barcode_photo_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            await conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.warning(f'Ошибка при добавлении отзыва - {e}')
            
    async def get_feedback(self, feedback_id):
        """Получение данных об отзыве"""
        try:
            logger.info('Получение данных об отзыве')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT * FROM feedbacks WHERE id = ?""", (feedback_id,))
            data = await cursor.fetchone()
            if data:
                return {'user_id': data[1], 'product_id': data[2], 'text': data[3], 'feedback_photo_id': data[4], 'barcode_photo_id': data[5], 'status': data[6], 'date': data[7]}
        except Exception as e:
            logger.warning(f'Ошибка при получении данных об отзыве - {e}')
            
    async def get_feedbacks(self):
        """Получение отзывов со статусом ожидания"""
        try:
            logger.info('Получение отзывов со статусом ожидания')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT id FROM feedbacks WHERE status = 0 ORDER BY date ASC""")
            return [a[0] for a in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении отзывов со статусом ожидания - {e}')
            
    async def get_feedbacks_with_admin_filter(self, admin_id: int = None):
        """Получение отзывов со статусом ожидания с фильтрацией по админу"""
        try:
            logger.info('Получение отзывов со статусом ожидания с фильтрацией по админу')  
            conn = await self.open()
            if admin_id:
                # Получаем отзывы только по товарам этого админа
                cursor = await conn.execute("""
                    SELECT f.id FROM feedbacks f 
                    JOIN products p ON f.product_id = p.id 
                    WHERE f.status = 0 AND p.admin_id = ?
                    ORDER BY f.date ASC
                """, (admin_id,))
            else:
                # Получаем все отзывы (для главного админа)
                cursor = await conn.execute("""SELECT id FROM feedbacks WHERE status = 0 ORDER BY date ASC""")
            return [a[0] for a in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении отзывов со статусом ожидания с фильтрацией по админу - {e}')
            return []
            
    async def get_feedback_waiting_days(self, feedback_id):
        """Получение времени ожидания отзыва"""
        try:
            logger.info('Получение времени ожидания отзыва')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT date FROM feedbacks WHERE id = ?""", (feedback_id,))
            date = await cursor.fetchone()
            if date:
                return (datetime.now() - datetime.strptime(date[0], "%Y-%m-%d %H:%M:%S")).days
            else:
                return 0
        except Exception as e:
            logger.warning(f'Ошибка при получении времени ожидания отзыва - {e}')
            return 0
            
    async def check_reg(self, user_id: int):
        """Проверка на регистрацию"""
        try:
            logger.info(f'Проверка на регистрацию')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id FROM users WHERE user_id = ?""", (user_id,))
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f'Ошибка при проверке на регистрацию - {e}')
            
    async def get_users(self):
        """Получение всех пользователей"""
        try:
            logger.info('Получение списка всех пользователей')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id FROM users""")
            return [a[0] for a in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении пользователей - {e}')   
            
    async def add_user(self, user_id: int):
        """Добавление пользователя"""
        try:
            logger.info(f'Добавление пользователя {user_id}')  
            conn = await self.open()
            await conn.execute("""INSERT OR IGNORE INTO users (user_id) VALUES (?)""", (user_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при добавлении пользователя - {e}')
            
    async def get_admins(self):
        """Получение всех админов"""
        try:
            logger.info('Получение списка всех админов')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id FROM admins""")
            return [a[0] for a in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении админов - {e}')   
            
    async def check_is_main_admin(self, user_id: int):
        """Проверка на главного админа"""
        try:
            logger.info(f'Проверка на главного админа')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id FROM admins WHERE user_id = ? AND is_main = 1""", (user_id,))
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f'Ошибка при проверке на главного админа - {e}')    
            
    async def check_is_admin(self, user_id: int):
        print(f"ПРОВЕРКА АДМИНА: user_id={user_id}")
        try:
            logger.info(f'Проверка на админа')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id FROM admins WHERE user_id = ?""", (user_id,))
            res = await cursor.fetchone()
            print(f"РЕЗУЛЬТАТ ПРОВЕРКИ: {res}")
            return res is not None
        except Exception as e:
            logger.warning(f'Ошибка при проверке на админа - {e}')       
            return False
            
    async def check_is_limited_admin(self, user_id: int):
        """Проверка на ограниченного админа"""
        try:
            logger.info(f'Проверка на ограниченного админа')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT user_id FROM admins WHERE user_id = ? AND is_limited = 1""", (user_id,))
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f'Ошибка при проверке на ограниченного админа - {e}')    
            return False
            
    async def add_admin(self, user_id: int, is_main: bool, is_limited: bool = False):
        print(f"ДОБАВЛЕНИЕ АДМИНА: user_id={user_id}, is_main={is_main}, is_limited={is_limited}")
        try:
            logger.info(f'Добавление админа {user_id}')  
            conn = await self.open()
            await conn.execute("""INSERT OR IGNORE INTO admins (user_id, is_main, is_limited) VALUES (?, ?, ?)""", (user_id, 1 if is_main else 0, 1 if is_limited else 0))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при добавлении админа - {e}')    
            
    async def del_admin(self, user_id: int):
        """Удаление админа"""
        try:
            logger.info(f'Удаление админа {user_id}')  
            conn = await self.open()
            await conn.execute("""DELETE FROM admins WHERE user_id = ?""", (user_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при удалении админа - {e}')          

    async def set_main_admin(self, user_id: int):
        """Назначение главного админа"""
        try:
            logger.info(f'Назначение главного админа {user_id}')
            conn = await self.open()
            # Сначала убираем главного админа у всех
            await conn.execute("""UPDATE admins SET is_main = 0""")
            # Затем назначаем нового главного админа
            await conn.execute("""UPDATE admins SET is_main = 1 WHERE user_id = ?""", (user_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при назначении главного админа - {e}')          

    async def add_product_request(self, user_id: int, payment_photo_id: str):
        """Добавление заявки на размещение товара"""
        try:
            logger.info(f'Добавление заявки на товар от {user_id}')
            conn = await self.open()
            await conn.execute("""INSERT INTO product_requests (user_id, payment_photo_id, status, created_at) VALUES (?, ?, 0, ?)""", 
                             (user_id, payment_photo_id, datetime.now().isoformat()))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при добавлении заявки на товар - {e}')

    async def get_product_requests(self, status: int = None):
        """Получение заявок на размещение товара"""
        try:
            logger.info('Получение заявок на товар')
            conn = await self.open()
            if status is not None:
                cursor = await conn.execute("""SELECT * FROM product_requests WHERE status = ? ORDER BY created_at DESC""", (status,))
            else:
                cursor = await conn.execute("""SELECT * FROM product_requests ORDER BY created_at DESC""")
            return await cursor.fetchall()
        except Exception as e:
            logger.warning(f'Ошибка при получении заявок на товар - {e}')
            return []

    async def approve_product_request(self, request_id: int):
        """Одобрение заявки на размещение товара"""
        try:
            logger.info(f'Одобрение заявки {request_id}')
            conn = await self.open()
            cursor = await conn.execute("SELECT * FROM product_requests WHERE id = ?", (request_id,))
            row = await cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                logger.warning(f'row={row}')
                logger.warning(f'columns={columns}')
                idx_platform = columns.index('platform') if 'platform' in columns else None
                logger.warning(f"idx_platform={idx_platform}")
                platform_val = row[idx_platform] if idx_platform is not None else None
                logger.warning(f"row[columns.index('platform')]={platform_val}")
                user_id = row[columns.index('user_id')]
                photo_id = row[columns.index('photo_id')]
                keywords = row[columns.index('name')]
                filter_ = row[columns.index('filter')]
                cashback = row[columns.index('cashback')]
                counts = row[columns.index('counts')]
                platform = platform_val
                logger.warning(f'approve_product_request: platform={platform} для заявки {request_id}')
                logger.warning(f'Перед add_product: platform={platform}')
                # Добавляем пользователя как ограниченного админа
                await self.add_user(user_id)
                await self.add_admin(user_id, False, True)
                # Лог перед add_product
                logger.warning(f'Перед add_product: platform={platform!r}, user_id={user_id}, photo_id={photo_id}, keywords={keywords}, counts={counts}, filter_={filter_}, cashback={cashback}')
                await self.add_product(photo_id, keywords.split(']#['), counts.split(']#['), filter_, cashback, user_id, platform)
                # Обновляем статус заявки
                await conn.execute("UPDATE product_requests SET status = 1 WHERE id = ?", (request_id,))
                await conn.commit()
                return user_id
        except Exception as e:
            logger.warning(f'Ошибка при одобрении заявки - {e}')
        return None

    async def reject_product_request(self, request_id: int):
        """Отклонение заявки на размещение товара"""
        try:
            logger.info(f'Отклонение заявки {request_id}')
            conn = await self.open()
            await conn.execute("""UPDATE product_requests SET status = 2 WHERE id = ?""", (request_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при отклонении заявки - {e}')

    async def get_product_request(self, request_id: int):
        """Получение конкретной заявки"""
        try:
            logger.info(f'Получение заявки {request_id}')
            conn = await self.open()
            cursor = await conn.execute("""SELECT * FROM product_requests WHERE id = ?""", (request_id,))
            return await cursor.fetchone()
        except Exception as e:
            logger.warning(f'Ошибка при получении заявки - {e}')
            return None

    async def get_last_product_request_id(self):
        """Получение ID последней заявки"""
        try:
            logger.info('Получение ID последней заявки')
            conn = await self.open()
            cursor = await conn.execute("""SELECT id FROM product_requests ORDER BY id DESC LIMIT 1""")
            result = await cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.warning(f'Ошибка при получении ID последней заявки - {e}')
            return None
            
    async def get_product(self, product_id: int | str) -> dict:
        """Получение данных товара"""
        try:
            logger.info('Получение данных товара')  
            conn = await self.open()
            cursor = await conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = await cursor.fetchone()
            if product:
                # Определяем индекс platform (если поле есть)
                columns = [col[0] for col in cursor.description]
                platform = None
                if 'platform' in columns:
                    platform = product[columns.index('platform')]
                return {
                    'photo_id': product[1], 
                    'keyword': product[2] if product[2] else "Не указано", 
                    'count': product[3] if product[3] else "0", 
                    'filter': product[4], 
                    'cashback': product[5],
                    'platform': platform
                }
            return {}
        except Exception as e:
            logger.warning(f'Ошибка при получении данных товара - {e}')
            return {}
            
    async def get_product_keywords(self, product_id: int | str) -> list:
        """Получение ключевых слов и количества"""
        try:
            logger.info(f'Получение ключевых слов и количества для продукта {product_id}')
            conn = await self.open()
            cursor = await conn.execute("""SELECT keywords, counts FROM products WHERE id = ?""", (product_id,))
            product = await cursor.fetchone()
            if product and product[0] and product[1]:
                keywords = product[0].split("]#[")
                counts = list(map(int, product[1].split("]#[")))
                return [[keyword, count] for keyword, count in zip(keywords, counts)]
            return [[f"Товар #{product_id}", 0]]
        except Exception as e:
            logger.error(f'Ошибка при получении ключевых слов и количества для продукта {product_id}: {e}')
            return [[f"Товар #{product_id}", 0]]
            
    async def get_product_name(self, product_id: int | str):
        """Получение имени товара"""
        try:
            logger.info('Получение имени товара')  
            conn = await self.open()
            cursor = await conn.execute("""SELECT keywords FROM products WHERE id = ?""", (product_id,))
            product = await cursor.fetchone()
            if product and product[0]:
                return self.random_split_text(product[0])
            else:
                return "Не указано"
        except Exception as e:
            logger.warning(f'Ошибка при получении имени товара - {e}')
            return "Не указано"
            
    async def get_products_id(self, admin_id: int = None) -> list[int]:
        """Получение id товаров"""
        try:
            logger.info(f'Получение id товаров')
            conn = await self.open()
            if admin_id:
                # Если указан admin_id, возвращаем только товары этого админа
                cursor = await conn.execute(f"""SELECT id FROM products WHERE admin_id = ?""", (admin_id,))
            else:
                # Если admin_id не указан, возвращаем все товары
                cursor = await conn.execute(f"""SELECT id FROM products""")
            return [row[0] for row in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении id товаров: {e}')
            return []
            
    async def get_products_id_where(self, user_id: int, table: str, is_located: bool) -> list[int]:
        """Получение id товаров, в которых пользователь не в ..."""
        try:
            logger.info(f'Получение id товаров, в которых пользователь {user_id} {"" if is_located else "не "}в {table}')
            conn = await self.open()
            cursor = await conn.execute(f"""SELECT p.id FROM products p WHERE p.id {'' if is_located else 'NOT '}IN (SELECT g.product_id FROM {table} g WHERE g.user_id = ?)""", (user_id,))
            product_ids = [row[0] for row in await cursor.fetchall()]
            
            # Фильтруем товары с нулевым количеством
            available_products = []
            for product_id in product_ids:
                keywords_data = await self.get_product_keywords(product_id)
                has_available = any(count > 0 for _, count in keywords_data)
                if has_available:
                    available_products.append(product_id)
            
            return available_products
        except Exception as e:
            logger.warning(f'Ошибка при получении id товаров, в которых пользователь {user_id} {"" if is_located else "не "}в {table}: {e}')
            return []
            
    async def get_products_for_feedback(self, user_id: int) -> list[int]:
        """Получение id товаров для согласования отзывов (участвует в раздаче, но не оставлял отзыв)"""
        try:
            logger.info(f'Получение товаров для отзывов пользователя {user_id}')
            conn = await self.open()
            # Получаем товары, в которых пользователь участвует в раздаче, но не оставлял отзыв
            cursor = await conn.execute("""
                SELECT DISTINCT g.product_id 
                FROM giveaways g 
                WHERE g.user_id = ? 
                AND g.product_id NOT IN (
                    SELECT f.product_id 
                    FROM feedbacks f 
                    WHERE f.user_id = ?
                )
            """, (user_id, user_id))
            product_ids = [row[0] for row in await cursor.fetchall()]
            
            return product_ids
        except Exception as e:
            logger.warning(f'Ошибка при получении товаров для отзывов пользователя {user_id}: {e}')
            return []
            
    async def add_product(self, photo_id: str, keywords: list, counts: list, filter: str, cashback: int, admin_id: int = None, platform: str = None):
        """Добавление товара с указанием админа и платформы"""
        try:
            logger.info(f'Добавление товара админом {admin_id}, platform={platform}')
            logger.warning(f'add_product: platform={platform} для admin_id={admin_id}')
            conn = await self.open()
            await conn.execute("INSERT INTO products (photo_id, keywords, counts, filter, cashback, admin_id, platform) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (photo_id, ']#['.join(keywords), ']#['.join(counts), filter, cashback, admin_id, platform))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при добавлении товара - {e}')

    async def get_last_product_id(self):
        """Получение ID последнего добавленного товара"""
        try:
            logger.info('Получение ID последнего добавленного товара')
            conn = await self.open()
            cursor = await conn.execute('SELECT id FROM products ORDER BY id DESC LIMIT 1')
            row = await cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning(f'Ошибка при получении ID последнего товара - {e}')
            return None

    async def get_product_admin(self, product_id: int):
        """Получение ID админа, создавшего товар"""
        try:
            logger.info(f'Получение админа товара {product_id}')
            conn = await self.open()
            cursor = await conn.execute("""SELECT admin_id FROM products WHERE id = ?""", (product_id,))
            result = await cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.warning(f'Ошибка при получении админа товара - {e}')
            return None


            
    async def _update_keywords_and_counts(self, product_id, data):
        """Обновление ключевых слов и количеств"""
        try:
            logger.info(f'Изменение ключевых слов и количеств')
            keywords = [item[0] for item in data]
            counts = [item[1] for item in data]
            keywords_string = "]#[".join(keywords)
            counts_string = "]#[".join(map(str, counts))
            conn = await self.open()
            await conn.execute("""UPDATE products SET keywords = ?, counts = ? WHERE id = ?""", (keywords_string, counts_string, product_id))
            await conn.commit()
        except Exception as e:
            logger.error(f'Ошибка при изменении ключевых слов и количеств: {e}')
            
    async def add_new_keyword(self, product_id, keyword, count):
        """Добавление нового ключевого слова"""
        try:
            logger.info(f'Добавление нового ключевого слова для {product_id}: keyword={keyword}, count={count}')
            if not isinstance(count, int) or count < 0:
                raise ValueError(f"Некорректное значение count: {count}")
            data = await self.get_product_keywords(product_id)
            data.append([keyword, count])
            await self._update_keywords_and_counts(product_id, data)
        except Exception as e:
            logger.error(f'Ошибка при добавлении ключевого слова для {product_id}: {e}')
        
    async def delete_keyword(self, product_id, index):
        """Добавление нового ключевого слова"""
        try:
            logger.info(f'Удаление ключевого слова для {product_id}')
            data = await self.get_product_keywords(product_id)
            del data[int(index)]
            await self._update_keywords_and_counts(product_id, data)
        except Exception as e:
            logger.error(f'Ошибка при добавлении ключевого слова для {product_id}: {e}')
            
    async def del_product(self, product_id):
        """Удаление товара"""
        try:
            logger.info(f'Удаление товара')  
            conn = await self.open()
            await conn.execute("""DELETE FROM products WHERE id = ?""", (product_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при удалении товара - {e}')   
            
    async def edit_product(self, product_id, param, new_value):
        """Изменение товара"""
        try:
            logger.info(f'Изменение товара')  
            conn = await self.open()
            await conn.execute(f"""UPDATE products SET {param} = ? WHERE id = ?""", (new_value, product_id))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при изменении товара - {e}')   
            
    async def open(self):
        return await aiosqlite.connect(self._filename)

    async def add_product_request_full(self, user_id: int, photo_id: str, name: str, filter: str, cashback: int, counts: str, platform: str = None):
        """Добавление полной заявки на товар, возвращает id заявки"""
        try:
            logger.info(f'Добавление полной заявки на товар от {user_id}, platform={platform}')
            conn = await self.open()
            cursor = await conn.execute("""
                INSERT INTO product_requests (user_id, payment_photo_id, status, created_at, name, filter, cashback, counts, photo_id, platform)
                VALUES (?, '', 0, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, datetime.now().isoformat(), name, filter, cashback, counts, photo_id, platform))
            await conn.commit()
            logger.warning(f'add_product_request_full: platform={platform} для user_id={user_id}')
            return cursor.lastrowid
        except Exception as e:
            logger.warning(f'Ошибка при добавлении полной заявки на товар - {e}')
            return None

    async def get_main_admins(self):
        """Получить user_id всех главных админов"""
        try:
            logger.info('Получение всех главных админов')
            conn = await self.open()
            cursor = await conn.execute('SELECT user_id FROM admins WHERE is_main = 1')
            return [row[0] for row in await cursor.fetchall()]
        except Exception as e:
            logger.warning(f'Ошибка при получении главных админов - {e}')
            return []

    async def get_product_requests_by_user(self, user_id: int, status: int = None):
        """Получить заявки пользователя, опционально по статусу"""
        try:
            logger.info(f'Получение заявок пользователя {user_id} со статусом {status}')
            conn = await self.open()
            if status is not None:
                cursor = await conn.execute("SELECT * FROM product_requests WHERE user_id = ? AND status = ? ORDER BY created_at DESC", (user_id, status))
            else:
                cursor = await conn.execute("SELECT * FROM product_requests WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return await cursor.fetchall()
        except Exception as e:
            logger.warning(f'Ошибка при получении заявок пользователя - {e}')
            return []

    async def save_payment_screenshot_to_request(self, request_id: int, file_id: str):
        """Сохраняет скрин оплаты в заявку (payment_photo_id)"""
        try:
            logger.info(f'Сохраняем скрин оплаты в заявку {request_id}')
            conn = await self.open()
            await conn.execute("UPDATE product_requests SET payment_photo_id = ? WHERE id = ?", (file_id, request_id))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при сохранении скрина оплаты - {e}')

    async def delete_user_draft_product_requests(self, user_id: int):
        """Удаляет все черновики (status=0) пользователя из product_requests"""
        try:
            logger.info(f'Удаление всех черновиков заявок пользователя {user_id}')
            conn = await self.open()
            await conn.execute("DELETE FROM product_requests WHERE user_id = ? AND status = 0", (user_id,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при удалении черновиков заявок пользователя - {e}')

    async def get_payment_settings(self):
        try:
            conn = await self.open()
            cursor = await conn.execute("SELECT requisites, amount FROM payment_settings WHERE id = 1")
            row = await cursor.fetchone()
            if row:
                return {'requisites': row[0], 'amount': row[1]}
            return {'requisites': '+3242424', 'amount': 0}
        except Exception as e:
            logger.warning(f'Ошибка при получении payment_settings - {e}')
            return {'requisites': '+3242424', 'amount': 0}

    async def set_payment_settings(self, requisites: str, amount: int):
        try:
            conn = await self.open()
            await conn.execute("UPDATE payment_settings SET requisites = ?, amount = ? WHERE id = 1", (requisites, amount))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при обновлении payment_settings - {e}')

    async def get_free_mode(self):
        try:
            conn = await self.open()
            cursor = await conn.execute("SELECT is_free_mode FROM payment_settings WHERE id = 1")
            row = await cursor.fetchone()
            return bool(row[0]) if row else False
        except Exception as e:
            logger.warning(f'Ошибка при получении is_free_mode - {e}')
            return False

    async def set_free_mode(self, is_free: bool):
        try:
            conn = await self.open()
            await conn.execute("UPDATE payment_settings SET is_free_mode = ? WHERE id = 1", (1 if is_free else 0,))
            await conn.commit()
        except Exception as e:
            logger.warning(f'Ошибка при обновлении is_free_mode - {e}')


db = DataBase(path.join(path.dirname(path.abspath(__file__)), getenv('DB_NAME')))
