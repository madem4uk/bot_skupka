from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from other import get_logger, bot
from typing import Callable, Optional

import utils as u
import logging


logger = get_logger(__name__)

# Главное меню пользователя (ReplyKeyboard)
def main_menu() -> ReplyKeyboardMarkup:
    btns = [
        [KeyboardButton(text="🏠 Меню")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=btns,
        resize_keyboard=True,
        input_field_placeholder="Открыть меню",
        one_time_keyboard=False
    )

async def main_menu_dynamic(user_id: int) -> ReplyKeyboardMarkup:
    """Динамическое главное меню в зависимости от статуса пользователя"""
    from database import db
    
    is_admin = await db.check_is_admin(user_id)
    
    if is_admin:
        # Для админов показываем кнопку "Админ панель" вместо "Свой товар"
        btns = [
            [KeyboardButton(text="🎁 Раздачи"), KeyboardButton(text="💸 Кешбек")],
            [KeyboardButton(text="📝 Согласовать отзыв"), KeyboardButton(text="🚨 Проблема")],
            [KeyboardButton(text="👑 Админ панель"), KeyboardButton(text="🚪 Выйти")]
        ]
    else:
        # Для обычных пользователей стандартное меню
        btns = [
            [KeyboardButton(text="🎁 Раздачи"), KeyboardButton(text="💸 Кешбек")],
            [KeyboardButton(text="📝 Согласовать отзыв"), KeyboardButton(text="🚨 Проблема")],
            [KeyboardButton(text="➕ Свой товар"), KeyboardButton(text="🚪 Выйти")]
        ]
    
    return ReplyKeyboardMarkup(
        keyboard=btns,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
        one_time_keyboard=False
    )

def main_menu_inline() -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="🎁 Текущие раздачи", callback_data="giveaways")],
        [InlineKeyboardButton(text="💸 Получить кешбек", callback_data="cashback"), InlineKeyboardButton(text="📝 Согласовать отзыв", callback_data="feedback")],
        [InlineKeyboardButton(text="🚨 Сообщить о проблеме", callback_data="problem")],
        [InlineKeyboardButton(text="➕ Хочу свой товар", callback_data="add_product")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

async def main_menu_inline_dynamic(user_id: int) -> InlineKeyboardMarkup:
    """Динамическое inline главное меню в зависимости от статуса пользователя"""
    from database import db
    
    is_admin = await db.check_is_admin(user_id)
    
    if is_admin:
        # Для админов показываем кнопку "Админ панель" вместо "Хочу свой товар"
        btns = [
            [InlineKeyboardButton(text="🎁 Текущие раздачи", callback_data="giveaways")],
            [InlineKeyboardButton(text="💸 Получить кешбек", callback_data="cashback"), InlineKeyboardButton(text="📝 Согласовать отзыв", callback_data="feedback")],
            [InlineKeyboardButton(text="🚨 Сообщить о проблеме", callback_data="problem")],
            [InlineKeyboardButton(text="👑 Админ панель", callback_data="admin_panel")]
        ]
    else:
        # Для обычных пользователей стандартное меню
        btns = [
            [InlineKeyboardButton(text="🎁 Текущие раздачи", callback_data="giveaways")],
            [InlineKeyboardButton(text="💸 Получить кешбек", callback_data="cashback"), InlineKeyboardButton(text="📝 Согласовать отзыв", callback_data="feedback")],
            [InlineKeyboardButton(text="🚨 Сообщить о проблеме", callback_data="problem")],
            [InlineKeyboardButton(text="➕ Хочу свой товар", callback_data="add_product")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=btns)

# Админ-меню

def admin_menu(is_main) -> ReplyKeyboardMarkup:
    btns = [
        [KeyboardButton(text="➕ Товар"), KeyboardButton(text="✏️ Редактировать")],
        [KeyboardButton(text="⏳ Ожидание"), KeyboardButton(text="💳 Оплаты")],
        [KeyboardButton(text="📢 Рассылка")]
    ]
    if is_main:
        btns.append([KeyboardButton(text="👑 Админы")])
    btns.append([KeyboardButton(text="🔙 В меню")])
    return ReplyKeyboardMarkup(
        keyboard=btns,
        resize_keyboard=True,
        input_field_placeholder="Админ-панель",
        one_time_keyboard=False
    )

def admin_menu_inline(is_main, is_limited=False, is_free_mode=False) -> InlineKeyboardMarkup:
    print(f"DEBUG: admin_menu_inline - is_main={is_main}, is_limited={is_limited}")
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    btns = []
    if is_limited:
        # Заменяем только первую кнопку на 'Добавить еще', остальные оставляем
        btns = [
            [InlineKeyboardButton(text="➕ Добавить еще", callback_data="add_product"), InlineKeyboardButton(text="✏️ Редактировать", callback_data="admin_edit_product")],
            [InlineKeyboardButton(text="⏳ Ожидание", callback_data="admin_pending"), InlineKeyboardButton(text="💳 Оплаты", callback_data="admin_payments")]
        ]
    else:
        btns = [
            [InlineKeyboardButton(text="➕ Товар", callback_data="admin_add_product"), InlineKeyboardButton(text="✏️ Редактировать", callback_data="admin_edit_product")],
            [InlineKeyboardButton(text="⏳ Ожидание", callback_data="admin_pending"), InlineKeyboardButton(text="💳 Оплаты", callback_data="admin_payments")]
        ]
        btns.append([InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_mailing")])
        if is_main:
            print(f"DEBUG: Добавляем кнопку '👑 Админы' для главного админа")
            btns.append([InlineKeyboardButton(text="👑 Админы", callback_data="admin_admins")])
            btns.append([InlineKeyboardButton(text=("Сделать бот бесплатным" if not is_free_mode else "Сделать бот платным"), callback_data="admin_toggle_free_mode")])
            btns.append([InlineKeyboardButton(text="💳 Реквизиты оплаты", callback_data="admin_payment_settings")])
    btns.append([InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_start")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

# Меню редактирования админов

def edit_admins() -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_admin"), InlineKeyboardButton(text="➖ Удалить", callback_data="delete_admin")],
        [InlineKeyboardButton(text="⭐ Сделать главным", callback_data="make_main_admin")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

# Да/Нет inline-кнопки (универсальные)
def yes_or_no_inline(callback_yes, callback_no) -> InlineKeyboardMarkup:
    btns = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=callback_yes),
            InlineKeyboardButton(text="❌ Нет", callback_data=callback_no)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

# Да/Нет reply-кнопки (если нужно)
def yes_or_no() -> ReplyKeyboardMarkup:
    btns = [[KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]]
    return ReplyKeyboardMarkup(
        keyboard=btns,
        resize_keyboard=True,
        input_field_placeholder="Выберите ответ",
        one_time_keyboard=False
    )

# Кнопка "Я всё понял" (регистрация)
def i_readed() -> InlineKeyboardMarkup:
    btns = [[InlineKeyboardButton(text='✅ Всё понятно', callback_data='reg_new_user')]]
    return InlineKeyboardMarkup(inline_keyboard=btns)

# Универсальная кнопка "Назад" (inline)
def back_inline(callback) -> InlineKeyboardMarkup:
    btns = [[InlineKeyboardButton(text='🔙 Назад', callback_data=callback)]]
    return InlineKeyboardMarkup(inline_keyboard=btns)

# Универсальная кнопка "В меню" (inline)
def to_menu_inline(callback) -> InlineKeyboardMarkup:
    btns = [[InlineKeyboardButton(text='🏠 В меню', callback_data=callback)]]
    return InlineKeyboardMarkup(inline_keyboard=btns)

# Универсальная кнопка "Назад" (reply)
def back_reply() -> ReplyKeyboardMarkup:
    btns = [[KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(
        keyboard=btns,
        resize_keyboard=True,
        one_time_keyboard=False
    )

# Универсальная кнопка "В меню" (reply)
def to_menu_reply() -> ReplyKeyboardMarkup:
    btns = [[KeyboardButton(text="🏠 В меню")]]
    return ReplyKeyboardMarkup(
        keyboard=btns,
        resize_keyboard=True,
        one_time_keyboard=False
    )

# --- InlineKeyboard ---
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def product_card_inline(product_id):
    btns = [
        [InlineKeyboardButton(text="➕ Добавить ещё ключевое слово", callback_data=f"add_keyword-{product_id}")],
        [InlineKeyboardButton(text="⏩ Продолжить", callback_data=f"continue-{product_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit-{product_id}"),
         InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete-{product_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def approve_reject_inline(item_id, approve_cb, reject_cb):
    btns = [
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"{approve_cb}-{item_id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"{reject_cb}-{item_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def pagination_inline(page, total_pages, cb_prefix, item_id=None):
    btns = []
    if page > 1:
        btns.append(InlineKeyboardButton(text="⬅️", callback_data=f"{cb_prefix}-prev-{page-1}"))
    if page < total_pages:
        btns.append(InlineKeyboardButton(text="➡️", callback_data=f"{cb_prefix}-next-{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[btns]) if btns else None


async def items_pages(callback: str, user_id, page: int = 1, back_to_menu: bool = False, admin_id: int = None) -> InlineKeyboardMarkup:
    logging.warning(f"items_pages: callback={callback}, user_id={user_id}, page={page}, back_to_menu={back_to_menu}, admin_id={admin_id}")
    try:
        maximum = 6
        data = await u.get_callback_list(callback, user_id, admin_id)
        builder = InlineKeyboardBuilder()
        if data and data[0]:
            total_items = len(data[0])
            total_pages = (total_items + maximum - 1) // maximum
            page = max(1, min(page, total_pages))
            start_index = (page - 1) * maximum
            end_index = start_index + maximum
            items_on_page = data[0][start_index:end_index]
            for item_id in items_on_page:
                try:
                    text = await data[1](item_id)
                    builder.row(InlineKeyboardButton(text=text, callback_data=f'{callback}-{item_id}'))
                except Exception as e:
                    builder.row(InlineKeyboardButton(text='...', callback_data=f'{callback}-{item_id}'))
            navigation_buttons = []
            if page > 1:
                navigation_buttons.append(InlineKeyboardButton(text='⏮️️', callback_data=f'page-{callback}-{page - 1}'))
            navigation_buttons.append(InlineKeyboardButton(text=f'▶️ {page if total_items > 0 else 0}/{total_pages} ◀️', callback_data='pass'))
            if page < total_pages:
                navigation_buttons.append(InlineKeyboardButton(text='⏭️', callback_data=f'page-{callback}-{page + 1}'))
            builder.row(*navigation_buttons)
        else:
            # Если список пустой — только одна кнопка
            builder.row(InlineKeyboardButton(text='Нет доступных товаров', callback_data='pass'))
        # Добавляем кнопку "Назад"
        if callback.startswith('admin_') or callback in ['edit_product', 'delete_admin', 'get_payment', 'check_feedback']:
            builder.row(InlineKeyboardButton(text='🔙 Назад в админ-меню', callback_data='back_to_admin'))
        elif callback == 'get_giveaway':
            builder.row(InlineKeyboardButton(text='🔙 Назад к раздачам', callback_data='back_to_giveaways'))
        else:
            builder.row(InlineKeyboardButton(text='🔙 Назад в меню', callback_data='back_to_start'))
        return builder.as_markup()
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')
        
        
def approve_or_reject_feedback(feedback_id) -> InlineKeyboardMarkup:
    try:
        btns = [
            [InlineKeyboardButton(text='✅ Одобрить', callback_data=f'approve_fb-{feedback_id}'), InlineKeyboardButton(text='❌ Отклонить', callback_data=f'reject_fb-{feedback_id}')],
            [InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')
        
        
def approve_or_reject_payment(payment_id) -> InlineKeyboardMarkup:
    try:
        btns = [
            [InlineKeyboardButton(text='💳 Оплачено', callback_data=f'approve_pm-{payment_id}'), InlineKeyboardButton(text='🚫 Отклонено', callback_data=f'reject_pm-{payment_id}')],
            [InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')
        

def reply_empty() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def create_one_btn(text, callback) -> InlineKeyboardMarkup:
    try:
        btns = [[InlineKeyboardButton(text=text, callback_data=callback)]]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')

def create_one_btn_admin_back(text, callback) -> InlineKeyboardMarkup:
    try:
        btns = [
            [InlineKeyboardButton(text=text, callback_data=callback)],
            [InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')


        

def start_add_giveaway(product_id) -> InlineKeyboardMarkup:
    try:
        btns = [
            [InlineKeyboardButton(text="✅ Я всё понял, готов выкупить товар", callback_data=f'redeem_giveaway-{product_id}')],
            [InlineKeyboardButton(text="🔙 Назад", callback_data='back_to_giveaways')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')
        
        
def edit_product(product_id, is_limited=False) -> InlineKeyboardMarkup:
    try:
        if is_limited:
            btns = [
                [InlineKeyboardButton(text='💰 Сумма кешбека', callback_data=f'edit_p_cashback-{product_id}')],
                [InlineKeyboardButton(text='🗑️ Удалить товар', callback_data=f'delete_product-{product_id}')],
                [InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="back_to_admin")]
            ]
        else:
            btns = [
                [InlineKeyboardButton(text='📸 Фото товара', callback_data=f'edit_p_photo_id-{product_id}'), InlineKeyboardButton(text='🔑 Ключевые слова', callback_data=f'change_keywords-{product_id}')],
                [InlineKeyboardButton(text='🔍 Фильтр для выкупа', callback_data=f'edit_p_filter-{product_id}'), InlineKeyboardButton(text='💰 Сумма кешбека', callback_data=f'edit_p_cashback-{product_id}')],
                [InlineKeyboardButton(text='🗑️ Удалить товар', callback_data=f'delete_product-{product_id}')],
                [InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="back_to_admin")]
            ]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')
        

def exit_from_giveaway(giveaway_id) -> InlineKeyboardMarkup:
    try:
        btns = [
            [InlineKeyboardButton(text="✅ Да", callback_data=f'exit_from_giveaway-{giveaway_id}'), InlineKeyboardButton(text="❌ Нет", callback_data='back_to_menu')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')
        
        
def add_new_keyword() -> InlineKeyboardMarkup:
    try:
        btns = [
            [InlineKeyboardButton(text="➕ Добавить", callback_data=f'add_new_keyword'), InlineKeyboardButton(text="⏩ Продолжить", callback_data='next_filter')],
            [InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')
        
        
def edit_keywords_product(product_id, keywords) -> InlineKeyboardMarkup:
    try:
        btns = []
        i = 0
        for k in keywords:
            btns.append([InlineKeyboardButton(text=f'{k[0]} - {k[1]}', callback_data=f'delete_keyword-{product_id}-{i}')])
            i += 1
        btns.append([InlineKeyboardButton(text=f'➕ Добавить ещё', callback_data=f'add_new_keyword-{product_id}')])
        return InlineKeyboardMarkup(inline_keyboard=btns)
    except Exception as e:
        logger.warning(f'Ошибка в кнопках: {e}')

def start_menu_inline() -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="Хочу купить с кешбеком", callback_data="open_main_menu")],
        [InlineKeyboardButton(text="Выставить свой товар", callback_data="open_admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def giveaways_catalog_nav(page, total, product_id):
    btns = []
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️ предыдущий товар", callback_data=f"giveaway_page-{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total}", callback_data="pass"))
    if page < total:
        nav.append(InlineKeyboardButton(text="▶️ следующий товар", callback_data=f"giveaway_page-{page+1}"))
    btns.append(nav)
    btns.append([InlineKeyboardButton(text="✅ Хочу участвовать", callback_data=f"get_giveaway-{product_id}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def agree_to_product_terms() -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="✅ Согласен с условиями", callback_data="agree_product_terms")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def approve_or_reject_product_request(request_id: int) -> InlineKeyboardMarkup:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    btns = [
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_product_request-{request_id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_product_request-{request_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def cashback_notification_with_pay_button() -> InlineKeyboardMarkup:
    """Кнопка для уведомления о кэшбеке с переходом к оплатам"""
    btns = [
        [InlineKeyboardButton(text="💳 Перейти к оплатам", callback_data="go_to_payments")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def add_new_keyword_user():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    btns = [
        [InlineKeyboardButton(text="➕ Добавить ещё ключевое слово", callback_data="add_new_keyword_user")],
        [InlineKeyboardButton(text="⏩ Продолжить", callback_data="continue_keywords_user")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def back_to_main_menu():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_start")]
    ])

def approve_or_reject_payment_request(request_id):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    btns = [
        [InlineKeyboardButton(text="✅ Оплата получена", callback_data=f"approve_payment_request-{request_id}"),
         InlineKeyboardButton(text="❌ Отклонить оплату", callback_data=f"reject_payment_request-{request_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def paid_button():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Я оплатил", callback_data="user_paid")]
    ])

def platform_choice_inline() -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="WB", callback_data="platform_WB")],
        [InlineKeyboardButton(text="OZON", callback_data="platform_OZON")],
        [InlineKeyboardButton(text="Яндексмаркет", callback_data="platform_Yandex")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)
