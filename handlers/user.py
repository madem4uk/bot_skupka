from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramAPIError

import sys;
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import markups as mk
import utils as u
from database import db
from other import get_logger, bot
from states import *
from states import AddProductRequestStates
import re


logger = get_logger(__name__)
router = Router()


@router.callback_query(F.data == 'reg_new_user', ~u.IsRegUserFilter())
async def reg_new_user(call: CallbackQuery):
    try:
        logger.info(f'Регистрация - {call.message.chat.id}')
        await db.add_user(call.message.chat.id)
        await call.message.delete()
        await call.message.answer(
            f'Здравствуйте, {call.from_user.first_name}! Вы успешно зарегистрировались и попали в главное меню', 
            reply_markup=mk.main_menu()
        )
    except Exception as e:
        logger.warning(f'Ошибка при изменении страницы пользователей: {e} - {call.message.chat.id}')
        
        
@router.message(F.text == '📝 Согласовать отзыв')
async def revocation_feedback(message: Message, state: FSMContext):
    try:
        logger.info(f'Согласование отзыва - {message.chat.id}')
        await message.answer('На какой товар хотите согласовать отзыв?', reply_markup=await mk.items_pages('select_product', message.chat.id))
        await state.set_state(RevocationFeedbackStates.product)
    except Exception as e:
        logger.warning(f'Ошибка при согласовании отзыва: {e} - {message.chat.id}')

@router.callback_query(F.data.startswith('select_product-'), StateFilter(RevocationFeedbackStates.product))
async def select_product(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Выбор товара для отзыва - {call.message.chat.id}')
        product_id = call.data.split('-')[1]
        await state.update_data(product_id=product_id)
        # Получаем keyword из participation/giveaways
        from database import db
        conn = await db.open()
        cursor = await conn.execute("SELECT keyword FROM giveaways WHERE user_id = ? AND product_id = ? ORDER BY rowid DESC LIMIT 1", (call.from_user.id, product_id))
        row = await cursor.fetchone()
        keyword = row[0] if row and row[0] else None
        if keyword:
            await state.update_data(**{f"keyword_{product_id}": keyword})
        await call.message.edit_text(
            text="✍️ Напишите текст отзыва (без фото)",
            reply_markup=mk.create_one_btn('🔙 Назад в меню', 'back_to_start')
        )
        await state.set_state(RevocationFeedbackStates.text)
    except Exception as e:
        logger.warning(f'Ошибка при выборе товара для отзыва: {e} - {call.message.chat.id}')

@router.message(StateFilter(RevocationFeedbackStates.text), F.text)
async def feedback_text_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Добавление текстового отзыва - {message.chat.id}')
        await state.update_data(feedback_text=message.text)
        await message.answer('🖼️ Пришлите фото разрезанного штрихкода', reply_markup=mk.create_one_btn('🔙 Назад в меню', 'back_to_start'))
        await state.set_state(RevocationFeedbackStates.barcode_photo_id)
    except Exception as e:
        logger.warning(f'Ошибка при добавлении текстового отзыва: {e} - {message.chat.id}')

@router.message(StateFilter(RevocationFeedbackStates.barcode_photo_id), F.photo)
async def barcode_photo_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Добавление отзыва с фото штрихкода - {message.chat.id}')
        data = await state.get_data()
        feedback_id = await db.add_feedback(message.chat.id, data['product_id'], data['feedback_text'], '', message.photo[-1].file_id)
        keyword = data.get(f"keyword_{data['product_id']}", None)
        if not keyword:
            # Пытаемся получить ключ из participation/giveaways
            try:
                conn = await db.open()
                cursor = await conn.execute("SELECT keyword FROM giveaways WHERE user_id = ? AND product_id = ? ORDER BY rowid DESC LIMIT 1", (message.from_user.id, data['product_id']))
                row = await cursor.fetchone()
                if row and row[0]:
                    keyword = row[0]
            except Exception as e:
                logger.warning(f'Ошибка при попытке получить ключ из participation: {e}')
        text = f"""
По запросу: <b>{keyword if keyword else 'Не указано'}</b>
ID клиента - <code>{message.from_user.id}</code>
Текст отзыва: {data['feedback_text']}
        """
        product_admin_id = await db.get_product_admin(data['product_id'])
        if product_admin_id:
            try:
                msg = await bot.send_photo(
                    chat_id=product_admin_id,
                    photo=message.photo[-1].file_id,
                    caption=text,
                    reply_markup=mk.approve_or_reject_feedback(feedback_id)
                )
            except Exception as e:
                logger.warning(f'Ошибка при отправке отзыва админу {product_admin_id}: {e}')
        else:
            logger.warning(f'У товара нет admin_id, отзыв не отправлен')
        await message.answer("✅ Отзыв отправлен на модерацию. Ожидайте уведомления о согласовании.")
    except Exception as e:
        logger.warning(f'Ошибка при добавлении отзыва с фото штрихкода: {e} - {message.chat.id}')
    finally:
        await state.clear()

# Удаляю все обработчики RevocationFeedbackStates.feedback_photo_id и RevocationFeedbackStates.barcode_photo_id
        
        
@router.message(F.text == "🎁 Раздачи")
async def giveaways(message: Message):
    try:
        logger.info(f'Раздачи - {message.chat.id}')
        await message.answer('📦 Выберите нужный товар раздачи', reply_markup=await mk.items_pages("get_giveaway", message.chat.id))
    except Exception as e:
        logger.warning(f'Ошибка при входе в меню раздач: {e} - {message.chat.id}')
        
        
@router.callback_query(F.data == 'back_to_giveaways')
async def back_to_giveaways(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Возврат в раздачи - {call.message.chat.id}')
        data = await u.get_callback_list("get_giveaway", call.from_user.id)
        product_ids = data[0] if data else []
        if not product_ids:
            await call.message.edit_text(
                "😕 К сожалению, сейчас нет доступных раздач.\n\nПопробуйте позже или обратитесь к администратору.",
                reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
            )
            return
        await show_giveaway_page(call, state, product_ids, 1)
    except Exception as e:
        logger.warning(f'Ошибка при возврате в раздачи: {e} - {call.message.chat.id}')

async def show_giveaway_page(call, state, product_ids, page):
    total = len(product_ids)
    if not (1 <= page <= total):
        await call.answer("Нет такой страницы")
        return
    product_id = product_ids[page-1]
    product = await db.get_product(product_id)
    keywords = product['keyword'].split(']#[')
    logger.warning(f'[DEBUG] product_id={product_id}, ВСЕ ключевые слова: {keywords}')
    available_keywords = []
    for keyword in keywords:
        is_avail = await db.check_product_availability(product_id, keyword)
        logger.warning(f'[DEBUG] product_id={product_id}, ключ: {keyword}, доступен: {is_avail}')
        if is_avail:
            available_keywords.append(keyword)
    logger.warning(f'[DEBUG] product_id={product_id}, ДОСТУПНЫЕ ключевые слова: {available_keywords}')
    if not available_keywords:
        await call.message.edit_media(
            media=InputMediaPhoto(media=product['photo_id'], caption="❌ Нет доступных ключевых слов для этого товара. Попробуйте позже."),
            reply_markup=mk.giveaways_catalog_nav(page, total, product_id)
        )
        await state.update_data(**{f"keyword_{product_id}": None})
        await state.set_state(JoinDistributionStates.product_id)
        await call.answer()
        return
    available_keyword = available_keywords[0]
    logger.warning(f'[DEBUG] product_id={product_id}, ВЫБРАНО для показа: {available_keyword}')
    platform = product.get('platform', None)
    if platform == 'Yandex':
        platform_human = 'Яндексмаркет'
    elif platform == 'WB':
        platform_human = 'WB'
    elif platform == 'OZON':
        platform_human = 'OZON'
    else:
        platform_human = platform if platform else None
    platform_str = f"\n<b>Платформа:</b> <code>{platform_human}</code>" if platform_human else ""
    caption = f"""
<code>{available_keyword}</code>{platform_str}

💸 <b>КЭШБЭК:</b> <code>{product['cashback']}₽</code> 💸
    """
    await call.message.edit_media(
        media=InputMediaPhoto(media=product['photo_id'], caption=caption),
        reply_markup=mk.giveaways_catalog_nav(page, total, product_id)
    )
    await state.update_data(**{f"keyword_{product_id}": available_keyword})
    await state.set_state(JoinDistributionStates.product_id)
    await call.answer()
        
        
@router.callback_query(F.data.startswith('get_giveaway-'))
async def get_giveaway(call: CallbackQuery, state: FSMContext):
    try:
        product_id = call.data.split('-')[1]
        logger.info(f'Получение раздачи {product_id} - {call.message.chat.id}')
        data = await state.get_data()
        available_keyword = data.get(f"keyword_{product_id}")
        product = await db.get_product(product_id)
        if not product:
            await call.message.answer('⛔ Такая раздача отсутствует')
            return
        # Если ключа нет или он закончился — подставляем первый доступный
        keywords = product['keyword'].split(']#[')
        available_keywords = []
        for keyword in keywords:
            is_avail = await db.check_product_availability(product_id, keyword)
            if is_avail:
                available_keywords.append(keyword)
        if not available_keywords:
            await call.message.answer('❌ Нет доступных ключевых слов для этого товара. Попробуйте позже.')
            return
        if not available_keyword or available_keyword not in available_keywords:
            available_keyword = available_keywords[0]
            await state.update_data(**{f"keyword_{product_id}": available_keyword})
        platform = product.get('platform', None)
        if platform == 'Yandex':
            platform_human = 'Яндексмаркет'
        elif platform == 'WB':
            platform_human = 'WB'
        elif platform == 'OZON':
            platform_human = 'OZON'
        else:
            platform_human = platform if platform else None
        platform_str = f"\n<b>Платформа:</b> <code>{platform_human}</code>" if platform_human else ""
        text = f"""
<code>{available_keyword}</code>{platform_str}

<b>⛔ ВНИМАТЕЛЬНО ПРОЧТИТЕ ВЕСЬ ТЕКСТ, ПЕРЕД ТЕМ КАК НАЖАТЬ ПРИНЯТЬ УЧАСТИЕ ⛔</b>

Все нужно делать через кнопки, если кнопки пропали, то пропишите /start
Если вы будете писать в бота, эти сообщения никто кроме вас не увидит, ТОЛЬКО КНОПКИ 🎯

<b>⬇️ Для участия выполните следующие шаги: ⬇️</b>

1. Найди наш товар по запросу "<b>{available_keyword}</b>"
2. Если не можешь найти товар, используй фильтр по бренду и введи "<b>{product['filter']}</b>"
3. Перейди в карточку товара и сделай заказ.
4. Присылай нам скриншот из доставки с видимым товаром и его ценой.
<b>🗑️ ВНИМАНИЕ</b>: Без скрина заказа, где четко видны товар и цена, участие в акции не засчитывается! 🗑️

<b>💸 СУММА КЭШБЭКА - {product['cashback']}P 💸</b>

❗ 1 аккаунт на WB = 1 единица любого товара из раздач ❗
"""
        await call.message.edit_media(media=InputMediaPhoto(media=product['photo_id'], caption=text), reply_markup=mk.start_add_giveaway(product_id))
        await state.set_state(JoinDistributionStates.product_id)
    except Exception as e:
        logger.warning(f'Ошибка при получении раздачи {product_id}: {e} - {call.message.chat.id}')

# Удаляю handler change_keyword полностью

@router.callback_query(StateFilter(JoinDistributionStates.product_id), F.data.startswith('redeem_giveaway-'))
async def take_part_giveaway(call: CallbackQuery, state: FSMContext):
    try:
        product_id = call.data.split('-')[1]
        logger.info(f'Принятие участия в раздаче {product_id} - {call.message.chat.id}')
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/giveaways_example.png")
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        # Создаем клавиатуру с кнопкой "Назад в каталог раздач"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в каталог раздач", callback_data="back_to_giveaways")]
        ])
        
        await call.message.edit_media(
            media=InputMediaPhoto(
                media=BufferedInputFile(file=file_bytes, filename='example.png'), 
                caption='🖼️ Пришлите скриншот заказанного товара'
            ),
            reply_markup=keyboard
        )
        await state.update_data(product_id=product_id)
        await state.set_state(JoinDistributionStates.photo_id)
    except Exception as e:
        logger.warning(f'Ошибка при получении раздачи {product_id}: {e} - {call.message.chat.id}')
        
        
@router.message(StateFilter(JoinDistributionStates.photo_id), F.photo)
async def add_order(message: Message, state: FSMContext):
    try:
        logger.info(f'Создание заказа - {message.chat.id}')
        data = await state.get_data()
        product_id = data['product_id']
        keyword = data.get(f"keyword_{product_id}")
        if not keyword:
            await message.answer("❌ Не выбран ключ для участия. Попробуйте заново.")
            return
        # Пытаемся добавить в раздачу
        success = await db.add_giveaway(message.chat.id, product_id, keyword)
        if not success:
            # Проверяем, есть ли другие доступные ключевые слова
            product = await db.get_product(product_id)
            keywords = product['keyword'].split(']#[')
            available_keywords = []
            for k in keywords:
                if await db.check_product_availability(product_id, k):
                    available_keywords.append(k)
            if available_keywords:
                # Показываем кнопки выбора других ключей
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=k, callback_data=f"choose_keyword_{product_id}_{k}")] for k in available_keywords
                    ]
                )
                await message.answer(
                    f"Ключевое слово <b>{keyword}</b> закончилось, но для этого товара ещё доступны другие ключевые слова.\nВыберите одно из них:",
                    reply_markup=kb
                )
                return
            else:
                await message.answer("❌ К сожалению, этот товар больше недоступен для участия в раздаче. Количество товара закончилось.")
                return
        # --- остальной код ---
        text = """
Благодарим за заказ 💙

🔷 Товар нужно забрать с пункта выдачи через 1-2 дня после поступления

🔷 Обязательно не выкидывайте упаковку со штрих кодом, его в дальнейшем нужно будет разрезать и прислать фото подтверждение

🔷 Далее когда заберете его из ПВЗ перейдите в меню и выберите пункт "Согласовать отзыв"
        """
        await message.answer(text, reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start"))
        # Получаем админа, создавшего товар
        product_admin_id = await db.get_product_admin(product_id)
        logger.info(f'DEBUG: product_id={product_id}, product_admin_id={product_admin_id}')
        if product_admin_id and product_admin_id != 0:
            # Отправляем уведомление только админу-создателю
            logger.info(f'DEBUG: Отправляем уведомление админу {product_admin_id}')
            try:
                admin_message = await message.copy_to(chat_id=product_admin_id)
                await bot.send_message(
                    chat_id=product_admin_id, 
                    text=f"Товар заказан!\nПо запросу: <b>{keyword}</b>\nID клиента - <code>{message.from_user.id}</code>",
                    reply_to_message_id=admin_message.message_id
                )
            except TelegramAPIError:
                logger.warning(f'Не удалось отправить уведомление админу {product_admin_id}')
        else:
            # Если admin_id не указан (старые товары) - отправляем всем админам
            logger.info(f'DEBUG: Отправляем уведомление всем админам (admin_id={product_admin_id})')
            await u.send_message_to_admins(text=f"Товар заказан!\nПо запросу: <b>{keyword}</b>\nID клиента - <code>{message.from_user.id}</code>", photos=[message.photo[-1].file_id])
    except Exception as e:
        logger.warning(f'Ошибка при получении фото отзыва: {e} - {message.chat.id}')
    finally:
        await state.clear()
        
        
@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(call: CallbackQuery):
    try:
        logger.info(f'Возврат на главное меню - {call.message.chat.id}')
        await call.message.delete()
        await call.message.answer(
            text="🏠 Вы вернулись в главное меню", 
            reply_markup=mk.main_menu()
        )
        await call.message.answer(
            "Выберите действие:",
            reply_markup=await mk.main_menu_inline_dynamic(call.message.chat.id)
        )
    except Exception as e:
        logger.warning(f'Ошибка при возвращении обратно: {e} - {call.message.chat.id}')
        
        
@router.callback_query(F.data.startswith('page-'))
async def change_page(call: CallbackQuery):
    try:
        logger.info(f'Изменение страницы - {call.message.chat.id}')
        await call.message.edit_reply_markup(reply_markup=await mk.items_pages(call.data.split('-')[1], call.message.chat.id, int(call.data.split('-')[2])))
    except Exception as e:
        logger.warning(f'Ошибка при изменении страницы: {e} - {call.message.chat.id}')
        

@router.callback_query(F.data == 'pass')
async def change_page(call: CallbackQuery):
    try:
        await call.answer()
    except Exception as e:
        logger.warning(f'Ошибка в pass: {e} - {call.message.chat.id}')
        
        
@router.message(F.text == "💰 Получить кешбек")
async def get_cashback(message: Message, state: FSMContext):
    await state.clear()
    try:
        logger.info(f'Вход в кешбек - {message.chat.id}')
        from database import db
        # Получаем все активные раздачи пользователя
        active_giveaways = await db.get_active_giveaways(message.chat.id)
        # Для каждой раздачи проверяем, есть ли согласованный отзыв
        for giveaway_id in active_giveaways:
            product_id = await db.get_product_with_giveaway(giveaway_id)
            # Проверяем, есть ли отзыв по этому товару
            conn = await db.open()
            cursor = await conn.execute("SELECT status FROM feedbacks WHERE user_id = ? AND product_id = ?", (message.chat.id, product_id))
            feedback = await cursor.fetchone()
            if not feedback or feedback[0] != 1:
                # Нет согласованного отзыва
                await message.answer(
                    "❗ Сначала согласуйте отзыв по товару, чтобы получить кешбек.",
                    reply_markup=mk.create_one_btn("Согласовать отзыв", "go_to_feedback")
                )
                return  # <--- Важно: сразу return, не продолжаем!
        await message.answer('Вы должны опубликовать отзыв строго через 2 дня после получения, раньше публиковать ЗАПРЕЩЕНО! Если 2 дня прошло, то оставьте отзыв на вб и пришлите скриншот опубликованного отзыва', 
                             reply_markup=mk.create_one_btn('Я всё понял', 'i_all_understand_cashback'))
    except Exception as e:
        logger.warning(f'Ошибка при входе в получение кешбека: {e} - {message.chat.id}')
        
        
@router.callback_query(F.data == 'i_all_understand_cashback')
async def get_cashback_2(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Запрос скрина отзыва или раздачи - {call.message.chat.id}')
        active_giveaways = await db.get_active_giveaways(call.message.chat.id)
        # --- ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ---
        for giveaway_id in active_giveaways:
            product_id = await db.get_product_with_giveaway(giveaway_id)
            conn = await db.open()
            cursor = await conn.execute("SELECT status FROM feedbacks WHERE user_id = ? AND product_id = ?", (call.message.chat.id, product_id))
            feedback = await cursor.fetchone()
            if not feedback or feedback[0] != 1:
                await call.message.edit_text(
                    "❗ Сначала согласуйте отзыв по товару, чтобы получить кешбек.",
                    reply_markup=mk.create_one_btn("Согласовать отзыв", "go_to_feedback")
                )
                await state.clear()
                return
        # --- КОНЕЦ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ ---
        if len(active_giveaways) > 1:
            await call.message.edit_text(text="🎁 Выберите нужную раздачу", reply_markup=await mk.items_pages('select_giveaway', call.message.chat.id))
            await state.set_state(GetCashbackStates.giveaway_id)
        elif len(active_giveaways) == 0:
           await call.message.edit_text(
               text='😕 Похоже, вы пока не участвуете ни в одной раздаче\n\n🎁 Чтобы присоединиться к раздачам, нажмите /start и выберите пункт "Раздачи" в меню\n',
               reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
           )
        else:
            # Проверка согласованного отзыва для единственной раздачи
            product_id = await db.get_product_with_giveaway(active_giveaways[0])
            conn = await db.open()
            cursor = await conn.execute("SELECT status FROM feedbacks WHERE user_id = ? AND product_id = ?", (call.message.chat.id, product_id))
            feedback = await cursor.fetchone()
            if not feedback or feedback[0] != 1:
                await call.message.edit_text(
                    "❗ Сначала согласуйте отзыв по товару, чтобы получить кешбек.",
                    reply_markup=mk.create_one_btn("Согласовать отзыв", "go_to_feedback")
                )
                await state.clear()
                return
            await call.message.edit_text(
                text="🖼️ Пришлите скриншот опубликованного отзыва",
                reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
            )
            await state.update_data(giveaway_id=active_giveaways[0])
            await state.set_state(GetCashbackStates.photo_id)
    except Exception as e:
        logger.warning(f'Ошибка при запросе скрина отзыва или раздачи: {e} - {call.message.chat.id}')
        
        
@router.callback_query(StateFilter(GetCashbackStates.giveaway_id), F.data.startswith('select_giveaway-'))
async def select_giveaway(call: CallbackQuery, state: FSMContext):
    logger.info(f"select_giveaway: callback_data={call.data}")
    try:
        logger.info(f'Выбор раздачи для выплаты - {call.message.chat.id}')
        giveaway_id = call.data.split('-')[1]
        product_id = await db.get_product_with_giveaway(giveaway_id)
        conn = await db.open()
        cursor = await conn.execute("SELECT status FROM feedbacks WHERE user_id = ? AND product_id = ?", (call.message.chat.id, product_id))
        feedback = await cursor.fetchone()
        if not feedback or feedback[0] != 1:
            await call.message.edit_text(
                "❗ Сначала согласуйте отзыв по товару, чтобы получить кешбек.",
                reply_markup=mk.create_one_btn("Согласовать отзыв", "go_to_feedback")
            )
            await state.clear()
            return
        await call.message.edit_text(
            text="🖼️ Пришлите скриншот опубликованного отзыва",
            reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
        )
        await state.update_data(giveaway_id=giveaway_id)
        await state.set_state(GetCashbackStates.photo_id)
    except Exception as e:
        logger.warning(f'Ошибка при выборе раздачи для выплаты: {e} - {call.message.chat.id}')
        
        
@router.message(StateFilter(GetCashbackStates.photo_id), F.photo)
async def cashback_photo_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    giveaway_id = data.get('giveaway_id')
    product_id = await db.get_product_with_giveaway(giveaway_id)
    conn = await db.open()
    cursor = await conn.execute("SELECT status FROM feedbacks WHERE user_id = ? AND product_id = ?", (message.chat.id, product_id))
    feedback = await cursor.fetchone()
    if not feedback or feedback[0] != 1:
        await message.answer("❗ Сначала согласуйте отзыв по товару, чтобы получить кешбек.", reply_markup=mk.create_one_btn("Согласовать отзыв", "go_to_feedback"))
        await state.clear()
        return
    try:
        logger.info(f'Запрос реквизитов - {message.chat.id}')
        await state.update_data(photo_id=message.photo[-1].file_id)
        await message.answer(
            "💳 Мы переведём оплату по номеру телефона.\nПришлите ваши данные для перевода по СБП:\nНомер телефона: +79999999999\nБанк: Сбер\nВ одном сообщении"
        )
        await state.set_state(GetCashbackStates.details)
    except Exception as e:
        logger.warning(f'Ошибка при запросе реквизитов: {e} - {message.chat.id}')
        
        
@router.message(StateFilter(GetCashbackStates.details), F.text)
async def cashback_details_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Добавление платежа - {message.chat.id}')
        data = await state.get_data()
        await message.answer("✅ Заявка отправлена! Ожидайте уведомления о выплате.", reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start"))
        
        product_id = await db.get_product_with_giveaway(data['giveaway_id'])
        await db.add_payment(message.chat.id, product_id, message.text, data['photo_id'])
        
        # Получаем админа товара и отправляем уведомление
        product_admin_id = await db.get_product_admin(product_id)
        # Получаем keyword из giveaways
        conn = await db.open()
        cursor = await conn.execute("SELECT keyword FROM giveaways WHERE user_id = ? AND product_id = ? ORDER BY rowid DESC LIMIT 1", (message.from_user.id, product_id))
        row = await cursor.fetchone()
        keyword = row[0] if row and row[0] else 'Не указано'
        if product_admin_id:
            try:
                admin_message = await message.copy_to(chat_id=product_admin_id)
                await bot.send_message(
                    chat_id=product_admin_id,
                    text=f"💰 <b>Новая заявка на кешбек</b>\n\n"
                         f"По запросу: <b>{keyword}</b>\n"
                         f"ID клиента: <code>{message.from_user.id}</code>\n"
                         f"Реквизиты: {message.text}",
                    reply_to_message_id=admin_message.message_id,
                    reply_markup=mk.cashback_notification_with_pay_button()
                )
            except TelegramAPIError:
                logger.warning(f'Не удалось отправить уведомление админу {product_admin_id}')
    except Exception as e:
        logger.warning(f'Ошибка при добавлении платежа: {e} - {message.chat.id}')
    finally:
        await state.clear()
        
        
@router.message(F.text == "🚪 Выйти из раздачи")
async def exit_giveaway_message(message: Message):
    try:
        logger.info(f'Выход из раздачи - {message.chat.id}')
        await message.answer('🗑️ Выберите раздачу для выхода', reply_markup=await mk.items_pages('exit_giveaway', message.chat.id))
    except Exception as e:
        logger.warning(f'Ошибка при выходе из раздачи: {e} - {message.chat.id}')


@router.message(F.text == "👑 Админ панель")
async def admin_panel(message: Message):
    try:
        logger.info(f'Открытие админ панели - {message.chat.id}')
        # Проверяем, является ли пользователь админом
        is_admin = await db.check_is_admin(message.chat.id)
        if not is_admin:
            await message.answer('❌ У вас нет доступа к админ панели')
            return
            
        is_main = await db.check_is_main_admin(message.chat.id)
        is_limited = await db.check_is_limited_admin(message.chat.id)
        
        await message.answer(
            text='👑 Админ панель',
            reply_markup=mk.admin_menu_inline(is_main, is_limited)
        )
    except Exception as e:
        logger.warning(f'Ошибка при открытии админ панели: {e} - {message.chat.id}')
        
        
@router.callback_query(F.data.startswith('exit_giveaway-'))
async def exit_giveaway(call: CallbackQuery):
    logger.info(f"exit_giveaway: callback_data={call.data}")
    try:
        logger.info(f'Выход из раздачи - {call.message.chat.id}')
        await call.message.edit_text('Вы уверены, что хотите выйти?', reply_markup=mk.exit_from_giveaway(call.data.split('-')[1]))
    except Exception as e:
        logger.warning(f'Ошибка при выходе из раздачи: {e} - {call.message.chat.id}')
        
        
@router.callback_query(F.data.startswith('exit_from_giveaway-'))
async def yes_exit_giveaway(call: CallbackQuery):
    try:
        logger.info(f'Успешный выход из раздачи - {call.message.chat.id}')
        await db.del_giveaway(call.data.split('-')[1])
        await call.message.edit_text('✅ Вы успешно вышли из раздачи')
    except Exception as e:
        logger.warning(f'Ошибка при выходе из раздачи: {e} - {call.message.chat.id}')
        

@router.message(F.text == "🚨 У меня возникла проблема")
async def problem(message: Message):
    try:
        logger.info(f'Выбор товара с проблемой - {message.chat.id}')
        await message.answer('�� С каким товаром возникла проблема?', reply_markup=await mk.items_pages('product_problem', message.chat.id))
    except Exception as e:
        logger.warning(f'Ошибка при выборе товара с проблемой: {e} - {message.chat.id}')
        

@router.callback_query(F.data.startswith('product_problem-'))
async def product_problem(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Запрос сообщения проблемы - {call.message.chat.id}')
        await state.update_data(product_id=call.data.split('-')[1])
        await call.message.edit_text('<b>⚠️ Писать строго при возникновении проблемы ⚠️</b>\n\nСообщения по типу «когда выплата?», «обязательно фото?» , «могу выкупить за 100% кешбек»\nОСТАНУТСЯ БЕЗ ОТВЕТА!!\n\nЦените свое и наше время!\n\n📝 Расскажите, что случилось? Вы можете отправить любые медиа файлы')
        await state.set_state(ProblemStates.message)
    except Exception as e:
        logger.warning(f'Ошибка при запросе сообщения проблемы: {e} - {call.message.chat.id}')
        
        
@router.message(StateFilter(ProblemStates.message))
async def send_product_problem(message: Message, state: FSMContext):
    try:
        logger.info(f'Отправка проблемы - {message.chat.id}')
        data = await state.get_data()
        await message.answer("✅ Сообщение о проблеме успешно отправлено администраторам")
        product_id = data['product_id']
        product_admin_id = await db.get_product_admin(product_id)
        main_admins = await db.get_main_admins()
        notified = set()
        # Получаем username пользователя и владельца карточки
        user_username = None
        admin_username = None
        try:
            user_obj = await bot.get_chat(message.from_user.id)
            user_username = f"@{user_obj.username}" if user_obj.username else f"<code>{user_obj.id}</code>"
        except Exception:
            user_username = f"<code>{message.from_user.id}</code>"
        try:
            admin_obj = await bot.get_chat(product_admin_id) if product_admin_id else None
            admin_username = f"@{admin_obj.username}" if admin_obj and admin_obj.username else (f"<code>{product_admin_id}</code>" if product_admin_id else "-")
        except Exception:
            admin_username = f"<code>{product_admin_id}</code>" if product_admin_id else "-"
        # Отправляем админу-владельцу
        if product_admin_id:
            try:
                admin_message = await message.copy_to(chat_id=product_admin_id)
                await bot.send_message(chat_id=product_admin_id, text=f'<b>ID клиента</b>: <code>{message.from_user.id}</code>\n<b>По запросу</b>: {await db.get_product_name(product_id)}', reply_to_message_id=admin_message.message_id)
                notified.add(product_admin_id)
            except TelegramAPIError:
                pass
        # Отправляем всем главным админам, кроме владельца (если он уже получил)
        for admin_id in main_admins:
            if admin_id == product_admin_id:
                continue
            try:
                admin_message = await message.copy_to(chat_id=admin_id)
                await bot.send_message(
                    chat_id=admin_id,
                    text=f'<b>ID клиента</b>: <code>{message.from_user.id}</code> ({user_username})\n<b>По запросу</b>: {await db.get_product_name(product_id)}\n<b>Владелец карточки</b>: {admin_username}',
                    reply_to_message_id=admin_message.message_id
                )
                notified.add(admin_id)
            except TelegramAPIError:
                continue
    except Exception as e:
        logger.warning(f'Ошибка при отправке проблемы: {e} - {message.chat.id}')
    finally:
        await state.clear()
        

@router.message(F.text == "📤 Разместить свой товар в боте")
async def public_product(message: Message):
    try:
        logger.info(f'Разместить свой товар - {message.chat.id}')
        await message.answer('🤝 По вопросам сотрудничества обращаться к @Root_Ai')
    except Exception as e:
        logger.warning(f'Ошибка в разместить свой товар: {e} - {message.chat.id}')

# Обработчик для главного inline-меню
from aiogram.types import CallbackQuery

# ДОБАВЛЯЕМ ЛОГИРОВАНИЕ В main_menu_inline_handler
@router.callback_query(F.data.in_("giveaways cashback feedback problem exit".split()))
async def main_menu_inline_handler(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Главное меню inline - {call.message.chat.id}')
        if call.data == 'giveaways':
            await call.message.edit_text('📦 Выберите нужный товар раздачи', reply_markup=await mk.items_pages("get_giveaway", call.message.chat.id))
        elif call.data == 'cashback':
            await call.message.edit_text('💰 Выберите раздачу для получения кешбека', reply_markup=await mk.items_pages("select_giveaway", call.message.chat.id))
        elif call.data == 'feedback':
            await call.message.edit_text('На какой товар хотите согласовать отзыв?', reply_markup=await mk.items_pages('select_product', call.message.chat.id))
            await state.set_state(RevocationFeedbackStates.product)
        elif call.data == 'problem':
            await call.message.edit_text('🚨 Выберите товар, с которым возникла проблема', reply_markup=await mk.items_pages('product_problem', call.message.chat.id))
            await state.set_state(ProblemStates.product)
        elif call.data == 'exit':
            await call.message.edit_text('🗑️ Выберите раздачу для выхода', reply_markup=await mk.items_pages('exit_giveaway', call.message.chat.id))
    except Exception as e:
        logger.warning(f'Ошибка при обработке главного меню inline: {e} - {call.message.chat.id}')


@router.callback_query(F.data == "admin_panel")
async def admin_panel_inline(call: CallbackQuery):
    try:
        logger.info(f'Открытие админ панели через inline - {call.message.chat.id}')
        # Проверяем, является ли пользователь админом
        is_admin = await db.check_is_admin(call.message.chat.id)
        if not is_admin:
            await call.answer('❌ У вас нет доступа к админ панели', show_alert=True)
            return
            
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        await call.message.edit_text(
            text='👑 Админ панель',
            reply_markup=mk.admin_menu_inline(is_main, is_limited)
        )
    except Exception as e:
        logger.warning(f'Ошибка при открытии админ панели через inline: {e} - {call.message.chat.id}')


@router.callback_query(F.data == "add_product")
async def start_add_product_request(call: CallbackQuery, state: FSMContext):
    await state.clear()  # Сбросить все старые данные FSM
    # Удалить все черновики заявок пользователя
    await db.delete_user_draft_product_requests(call.message.chat.id)
    # Проверяем, ограниченный ли это админ
    is_limited = await db.check_is_limited_admin(call.message.chat.id)
    if is_limited:
        await call.message.edit_text(
            "📷 Пришлите фото товара для заявки",
            reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
        )
        await state.update_data(keywords=[])
        await state.update_data(counts=[])
        await state.set_state(AddProductRequestStates.photo)
    else:
        # Для обычных пользователей и неограниченных админов — стандартный флоу
        await call.message.edit_text(
            "📷 Пришлите фото товара для заявки",
            reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
        )
        await state.update_data(keywords=[])
        await state.update_data(counts=[])
        await state.set_state(AddProductRequestStates.photo)

@router.message(StateFilter(AddProductRequestStates.photo), F.photo)
async def add_product_request_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await message.answer(
        "Выберите площадку, на которой будет размещён товар:",
        reply_markup=mk.platform_choice_inline()
    )
    await state.set_state(AddProductRequestStates.platform)

@router.callback_query(StateFilter(AddProductRequestStates.platform), F.data.startswith("platform_"))
async def add_product_request_platform(call: CallbackQuery, state: FSMContext):
    platform = call.data.replace("platform_", "")
    await state.update_data(platform=platform)
    await call.message.edit_text(f"Площадка выбрана: {platform}\n\nПришлите запрос по которому покупатель должен будет найти и выкупить ваш товар.")
    await state.set_state(AddProductRequestStates.name)

@router.message(StateFilter(AddProductRequestStates.name), F.text)
async def add_product_request_keyword(message: Message, state: FSMContext):
    data = await state.get_data()
    keywords = data.get('keywords', [])
    keywords.append(message.text)
    await state.update_data(keywords=keywords)
    await message.answer("🔢 Пришлите количество для этого ключевого слова")
    await state.set_state(AddProductRequestStates.count)

@router.message(StateFilter(AddProductRequestStates.count), F.text)
async def add_product_request_count(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Введите положительное число!")
        return
    data = await state.get_data()
    counts = data.get('counts', [])
    counts.append(message.text)
    await state.update_data(counts=counts)
    await message.answer(
        '✅ Ключевое слово и количество добавлены!',
        reply_markup=mk.add_new_keyword_user()
    )
    await state.set_state(AddProductRequestStates.keyword_action)

@router.callback_query(StateFilter(AddProductRequestStates.keyword_action), F.data == "add_new_keyword_user")
async def add_new_keyword_user_cb(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("✍️ Пришлите ключевое слово для выкупа (например, название товара)")
    await state.set_state(AddProductRequestStates.name)

@router.callback_query(StateFilter(AddProductRequestStates.keyword_action), F.data == "continue_keywords_user")
async def continue_keywords_user_cb(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🔎 Пришлите фильтр для поиска (например, название бренда)")
    await state.set_state(AddProductRequestStates.filter)

@router.message(StateFilter(AddProductRequestStates.filter), F.text)
async def add_product_request_filter(message: Message, state: FSMContext):
    await state.update_data(filter=message.text)
    await message.answer("💸 Пришлите сумму кешбека в рублях (только число)")
    await state.set_state(AddProductRequestStates.cashback)

@router.message(StateFilter(AddProductRequestStates.cashback), F.text)
async def add_product_request_cashback(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только число!")
        return
    await state.update_data(cashback=int(message.text))
    data = await state.get_data()
    # Сохраняем заявку в product_requests (статус 0 - черновик)
    request_id = await db.add_product_request_full(
        message.chat.id,
        data['photo_id'],
        ']#['.join(data['keywords']),
        data['filter'],
        data['cashback'],
        ']#['.join(data['counts']),
        data.get('platform', None)
    )
    if not request_id:
        await message.answer("❌ Ошибка при создании заявки. Попробуйте позже.")
        return
    # Проверяем режим оплаты
    is_free = await db.get_free_mode()
    if is_free:
        await message.answer("Ваша заявка отправлена на подтверждение админу. Ожидайте решения.", reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start"))
        main_admins = await db.get_main_admins()
        for admin_id in main_admins:
            try:
                await bot.send_photo(
                    int(admin_id),
                    data['photo_id'],
                    caption=f"Новая заявка на товар (БЕСПЛАТНО)\nПользователь: <code>{message.from_user.id}</code>\nКлючевые слова: {']#['.join(data['keywords'])}\nФильтр: {data['filter']}\nКешбек: {data['cashback']}₽",
                    reply_markup=mk.approve_or_reject_payment_request(request_id)
                )
            except Exception:
                pass
        await state.clear()
        return
    # Если не бесплатный — обычный флоу оплаты
    payment_settings = await db.get_payment_settings()
    requisites = payment_settings['requisites']
    amount = payment_settings['amount']
    await message.answer(
        f"Оплатите сумму <b>{amount if amount else data['cashback']}₽</b> по реквизитам: <code>{requisites}</code>\n\nПосле оплаты нажмите кнопку ниже.",
        reply_markup=mk.paid_button()
    )
    await state.update_data(request_id=request_id)
    await state.set_state(AddProductRequestStates.waiting_payment_button)

@router.message(StateFilter(AddProductRequestStates.waiting_payment), F.photo)
async def handle_payment_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    request_id = data.get('request_id')
    if request_id:
        req = await db.get_product_request(request_id)
        if not req:
            await message.answer("❌ Не найдена активная заявка для оплаты.")
            return
    else:
        # Fallback: ищем последнюю заявку со статусом 0
        requests = await db.get_product_requests_by_user(message.chat.id, status=0)
        if not requests:
            await message.answer("❌ Не найдена активная заявка для оплаты.")
            return
        req = requests[-1]
        request_id = req[0]
    await db.save_payment_screenshot_to_request(request_id, message.photo[-1].file_id)
    import logging
    logging.warning(f'Содержимое req для заявки {request_id}: {req}')
    keywords = data.get('keywords', [])
    counts = data.get('counts', [])
    if (not keywords or not counts) and req[5]:
        keywords = req[5].split(']#[')
        if len(req) > 8 and req[8]:
            counts = req[8].split(']#[')
        else:
            counts = ['1'] * len(keywords)
    kw_str = '\n'.join([f"{k} - {c} шт." for k, c in zip(keywords, counts)])
    # --- Только главным админам ---
    main_admins = await db.get_main_admins()
    user_info = f"<code>{message.from_user.id}</code>"
    for admin_id in main_admins:
        try:
            logger.warning(f'Отправка фото товара админу {admin_id}: file_id={req[-2]}')
            await bot.send_photo(
                int(admin_id),
                req[-2],
                caption=f"Новая заявка на товар\nПользователь: {user_info}\nКлючевые слова и количества:\n{kw_str}\nФильтр: {req[6]}\nКешбек: {req[7]}₽"
            )
            logger.warning(f'Отправка скрина оплаты админу {admin_id}: file_id={message.photo[-1].file_id}')
            await bot.send_photo(
                int(admin_id),
                message.photo[-1].file_id,
                caption=f"Скрин оплаты по заявке #{request_id}\nПользователь: {user_info}",
                reply_markup=mk.approve_or_reject_payment_request(request_id)
            )
        except Exception as e:
            logger.warning(f'Ошибка при отправке уведомления админу {admin_id}: {e}')
    await message.answer("✅ Скрин оплаты отправлен на проверку. Ожидайте подтверждения.")
    await state.set_state(AddProductRequestStates.waiting_payment_check)

@router.callback_query(F.data == "user_paid", StateFilter(AddProductRequestStates.waiting_payment_button))
async def user_paid_handler(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    # Жёстко сбрасываем все старые FSM и переводим только в waiting_payment
    await state.clear()
    await state.set_state(AddProductRequestStates.waiting_payment)
    await call.message.answer(
        "Пожалуйста, пришлите скриншот оплаты в ответ на это сообщение.",
        reply_markup=mk.back_to_main_menu()
    )
    import logging
    logging.warning(f"user_paid_handler: user_id={call.from_user.id}, FSM set to waiting_payment")

@router.message(F.text == "🏠 Меню")
async def show_main_menu(message: Message):
    await message.answer(
        "Главное меню:",
        reply_markup=mk.main_menu()
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=await mk.main_menu_inline_dynamic(message.chat.id)
    )

@router.callback_query(F.data.in_(["back_to_start", "back_to_menu", "back_to_main_menu", "back_to_user_menu"]))
async def back_to_main_menu(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        "Главное меню:",
        reply_markup=mk.main_menu()
    )
    await call.message.answer(
        "Выберите действие:",
        reply_markup=await mk.main_menu_inline_dynamic(call.message.chat.id)
    )

@router.callback_query(F.data == 'go_to_feedback')
async def go_to_feedback_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('На какой товар хотите согласовать отзыв?', reply_markup=await mk.items_pages('select_product', call.from_user.id))
    await state.set_state(RevocationFeedbackStates.product)
    await call.answer()
