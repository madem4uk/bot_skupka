from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.types import InputMediaPhoto

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import markups as mk
import utils as u
from database import db
from other import get_logger
from handlers.user import giveaways, get_cashback, revocation_feedback, problem, public_product, JoinDistributionStates, RevocationFeedbackStates
from states import GetCashbackStates

logger = get_logger(__name__)
router = Router()

@router.message(CommandStart())
async def start(message: Message):
    await db.add_user(message.chat.id)
    await message.answer(
        "Главное меню:",
        reply_markup=mk.main_menu()
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=await mk.main_menu_inline_dynamic(message.chat.id)
    )

# Обработка нажатий на стартовые кнопки
from aiogram.types import CallbackQuery

async def show_admin_panel(chat_id, send_func, is_inline=False):
    is_admin = await db.check_is_admin(chat_id)
    if not is_admin:
        await send_func('⛔ У вас нет прав администратора.')
        return
    is_main = await db.check_is_main_admin(chat_id)
    is_limited = await db.check_is_limited_admin(chat_id)
    print(f"DEBUG: show_admin_panel - chat_id={chat_id}, is_main={is_main}, is_limited={is_limited}")
    if is_inline:
        await send_func('Выберите действие', reply_markup=mk.admin_menu_inline(is_main, is_limited))
    else:
        await send_func('Выберите действие', reply_markup=mk.admin_menu(is_main))

@router.callback_query(F.data == "open_admin_panel")
async def open_admin_panel(call: CallbackQuery):
    await show_admin_panel(call.from_user.id, lambda text, **kwargs: call.message.edit_text(text, **kwargs), is_inline=True)
    await call.answer()

@router.callback_query(F.data == "open_main_menu")
async def open_main_menu(call: CallbackQuery):
    await call.message.edit_text(
        "Главное меню:",
        reply_markup=await mk.main_menu_inline_dynamic(call.message.chat.id)
    )
    await call.answer()

@router.callback_query(F.data == "giveaways")
async def cb_giveaways(call: CallbackQuery, state: FSMContext):
    data = await u.get_callback_list("get_giveaway", call.from_user.id)
    product_ids = data[0] if data else []
    if not product_ids:
        await call.message.edit_text(
            "😕 К сожалению, сейчас нет доступных раздач.\n\nПопробуйте позже или обратитесь к администратору.",
            reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
        )
        await call.answer()
        return
    await show_giveaway_page(call, state, product_ids, 1)

@router.callback_query(F.data.startswith("giveaway_page-"))
async def cb_giveaway_page(call: CallbackQuery, state: FSMContext):
    page = int(call.data.split('-')[1])
    data = await u.get_callback_list("get_giveaway", call.from_user.id)
    product_ids = data[0] if data else []
    await show_giveaway_page(call, state, product_ids, page)

async def show_giveaway_page(call, state, product_ids, page):
    total = len(product_ids)
    if not (1 <= page <= total):
        await call.answer("Нет такой страницы")
        return
    product_id = product_ids[page-1]
    product = await db.get_product(product_id)
    
    # Получаем первое доступное ключевое слово
    keywords = product['keyword'].split(']#[')
    available_keyword = keywords[0] if keywords else "Не указано"
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
    # Формируем текст с ключевым словом, платформой и кешбеком
    caption = f"""
<code>{available_keyword}</code>{platform_str}

💸 <b>КЭШБЭК:</b> <code>{product['cashback']}₽</code> 💸
    """
    
    await call.message.edit_media(
        media=InputMediaPhoto(media=product['photo_id'], caption=caption),
        reply_markup=mk.giveaways_catalog_nav(page, total, product_id)
    )
    await state.update_data(keyword=product['keyword'])
    await state.set_state(JoinDistributionStates.product_id)
    await call.answer()

@router.callback_query(F.data == "cashback")
async def cb_cashback(call: CallbackQuery, state: FSMContext):
    # Проверяем активные раздачи
    active_giveaways = await db.get_active_giveaways(call.from_user.id)
    
    # Проверяем, есть ли одобренные отзывы
    approved_feedbacks = await db.get_products_for_feedback(call.from_user.id)
    
    if len(active_giveaways) > 1:
        await call.message.edit_text(text="🎁 Выберите нужную раздачу", reply_markup=await mk.items_pages('select_giveaway', call.from_user.id))
        await state.set_state(GetCashbackStates.giveaway_id)
    elif len(active_giveaways) == 0:
        await call.message.edit_text(
            text='😕 Похоже, вы пока не участвуете ни в одной раздаче\n\n🎁 Чтобы присоединиться к раздачам, выберите "Раздачи" в меню',
            reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
        )
    else:
        # Если есть активная раздача, проверяем статус отзыва
        product_id = await db.get_product_with_giveaway(active_giveaways[0])
        feedback_status = await db.get_feedback_status(call.from_user.id, product_id)
        
        if feedback_status == 1:  # Отзыв одобрен
            # Показываем выбор раздачи для получения кешбека
            await call.message.edit_text(text="🎁 Выберите нужную раздачу", reply_markup=await mk.items_pages('select_giveaway', call.from_user.id))
            await state.set_state(GetCashbackStates.giveaway_id)
        else:
            # Отзыв не одобрен или его нет - сразу просим согласовать
            await call.message.edit_text(
                text="❗ Сначала согласуйте отзыв по товару, чтобы получить кешбек.",
                reply_markup=mk.create_one_btn("Согласовать отзыв", "go_to_feedback")
            )
            await state.clear()
    await call.answer()

@router.callback_query(F.data == "feedback")
async def cb_feedback(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('На какой товар хотите согласовать отзыв?', reply_markup=await mk.items_pages('select_product', call.from_user.id))
    await state.set_state(RevocationFeedbackStates.product)
    await call.answer()

@router.callback_query(F.data == "problem")
async def cb_problem(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('📦 С каким товаром возникла проблема?', reply_markup=await mk.items_pages('product_problem', call.from_user.id))
    await call.answer()

@router.callback_query(F.data == "exit")
async def cb_exit(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Выберите нужную раздачу для выхода", reply_markup=await mk.items_pages('exit_giveaway', call.from_user.id))
    await call.answer()

@router.callback_query(F.data == "back_to_start")
async def cb_back_to_start(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        "Главное меню:",
        reply_markup=mk.main_menu()
    )
    await call.message.answer(
        "Выберите действие:",
        reply_markup=await mk.main_menu_inline_dynamic(call.message.chat.id)
    )

@router.message(Command('admin'))
async def admin(message: Message):
    print(f"/admin вызван пользователем {message.chat.id}")
    logger.info(f'/admin вызван пользователем {message.chat.id}')
    is_admin = await db.check_is_admin(message.chat.id)
    print(f"is_admin={is_admin}, chat_id={message.chat.id}")
    logger.info(f'is_admin={is_admin}, chat_id={message.chat.id}')
    if not is_admin:
        await message.answer('⛔ У вас нет прав администратора.')
        return
    try:
        logger.info(f'Открытие меню админа - {message.chat.id}')
        print(f'Открытие меню админа - {message.chat.id}')
        await show_admin_panel(message.chat.id, lambda text, **kwargs: message.answer(text, **kwargs), is_inline=True)
    except Exception as e:
        logger.warning(f'Ошибка при просмотре меню админа: {e} - {message.chat.id}')
        print(f'Ошибка при просмотре меню админа: {e} - {message.chat.id}')
    