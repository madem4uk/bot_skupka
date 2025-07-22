from aiogram import Router
from aiogram.types import Message, InputFile, URLInputFile, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from aiogram.filters import Filter
from typing import Optional, Union, List
from aiogram.exceptions import TelegramAPIError

from database import db
from other import bot, get_logger


router = Router()
logger = get_logger(__name__)
    

class AdminFilter(Filter):
    """Проверка на админа бота"""
    async def __call__(self, message: Message) -> bool:
        return await db.check_is_admin(message.from_user.id)
    
    
class IsDigitFilter(Filter):
    """Проверка на число"""
    async def __call__(self, message: Message) -> bool:
        return message.text.isdigit()
    
    
class IsMainAdminFilter(Filter):
    """Проверка на главного админа"""
    async def __call__(self, message: Message) -> bool:
        return await db.check_is_main_admin(message.from_user.id)
    
    
class IsRegUserFilter(Filter):
    """Проверка на регистрацию"""
    async def __call__(self, message: Message) -> bool:
        return await db.check_reg(message.from_user.id)
    
    
async def get_callback_list(callback, user_id, admin_id=None):
    async def get_username(us_id):
        user = await bot.get_chat(chat_id=us_id)
        return f"@{user.username}" if user.username else f'@{user.username} - {us_id}'
    async def get_product_name(product_id):
        product = await db.get_product_name(product_id)
        return product
    async def get_payment_name(payment_id):
        try:
            data = await db.get_payment_data(payment_id)
            return f'{data[0]} - {data[1]}руб.'
        except TelegramAPIError:
            return f'{data[0]} - {data[1]}руб.'
    async def get_giveaway_name(giveaway_id):
        return await db.get_giveaway_name(giveaway_id)
    async def get_feedback_name(feedback_id):
        user = await db.get_user_from_feedback(feedback_id)
        try:
            user_data = await bot.get_chat(user)
        except TelegramAPIError:
            user_data = None
        days = await db.get_feedback_waiting_days(feedback_id)
        if user_data and days >= 0:
            return f'@{user_data.username} - {days} дней'
        elif days >= 0:
            return f'{user} - {days} дней'
        else:
            return str(user)
    async def get_etc_name(param):
        return param
        
    async def get_keyword_from_giveaway(product_id):
        conn = await db.open()
        cursor = await conn.execute("SELECT keyword FROM giveaways WHERE user_id = ? AND product_id = ? ORDER BY rowid DESC LIMIT 1", (user_id, product_id))
        row = await cursor.fetchone()
        return row[0] if row and row[0] else f"Товар #{product_id}"
    async def get_keyword_from_giveaway_id(giveaway_id):
        conn = await db.open()
        cursor = await conn.execute("SELECT keyword FROM giveaways WHERE id = ?", (giveaway_id,))
        row = await cursor.fetchone()
        return row[0] if row and row[0] else f"Раздача #{giveaway_id}"
    callbacks = {'delete_admin': [await db.get_admins(), get_username],
                 'select_giveaway': [await db.get_active_giveaways(user_id), get_keyword_from_giveaway_id],
                 'select_product': [await db.get_products_for_feedback(user_id), get_keyword_from_giveaway],
                 'get_giveaway': [await db.get_products_id_where(user_id, 'giveaways', False), get_product_name],
                 'get_payment': [await db.get_payments(admin_id), get_payment_name],
                 'edit_product': [await db.get_products_id(admin_id), get_product_name],
                 'exit_giveaway': [await db.get_active_giveaways(user_id), get_giveaway_name],
                 'product_problem': [await db.get_products_id_where(user_id, 'giveaways', True), get_product_name],
                 'check_feedback': [await db.get_feedbacks_with_admin_filter(admin_id), get_feedback_name]}
    return callbacks.get(callback) if callback in callbacks else [[], get_etc_name]


async def send_message_to_admins(text: str = None,
    photos: Optional[List[Union[str, InputFile, URLInputFile]]] = None,
    videos: Optional[List[Union[str, InputFile, URLInputFile]]] = None,
    documents: Optional[List[Union[str, InputFile, URLInputFile]]] = None,
    **kwargs):
    
    if all(arg is None for arg in (text, photos, videos, documents)):
        raise ValueError("Хотя бы 1 из параметров должен быть указан")
    messages = {}
    for admin in await db.get_admins():
        try:
            if photos and len(photos) > 1:
                media_group = [InputMediaPhoto(media=photo, caption=text if i == 0 else None) for i, photo in enumerate(photos)]
                message = await bot.send_media_group(chat_id=admin, media=media_group, **kwargs)
            elif videos and len(videos) > 1:
                media_group = [InputMediaVideo(media=video, caption=text if i == 0 else None) for i, video in enumerate(videos)]
                message = await bot.send_media_group(chat_id=admin, media=media_group, **kwargs)
            elif documents and len(documents) > 1:
                media_group = [InputMediaDocument(media=doc, caption=text if i == 0 else None) for i, doc in enumerate(documents)]
                message = await bot.send_media_group(chat_id=admin, media=media_group, **kwargs)
            elif photos:
                message = await bot.send_photo(chat_id=admin, photo=photos[0], caption=text, **kwargs)
            elif videos:
                message = await bot.send_video(chat_id=admin, video=videos[0], caption=text, **kwargs)
            elif documents:
                message = await bot.send_document(chat_id=admin, document=documents[0], caption=text, **kwargs)
            else:
                message = await bot.send_message(chat_id=admin, text=text, **kwargs)
            messages[admin] = message
        except Exception as e:
            logger.warning(f'Ошибка при отправке сообщения админу {admin} - {e}')
            continue
    return messages


async def send_message_to_main_admins(text: str = None,
    photos: Optional[List[Union[str, InputFile, URLInputFile]]] = None,
    videos: Optional[List[Union[str, InputFile, URLInputFile]]] = None,
    documents: Optional[List[Union[str, InputFile, URLInputFile]]] = None,
    **kwargs):
    if all(arg is None for arg in (text, photos, videos, documents)):
        raise ValueError("Хотя бы 1 из параметров должен быть указан")
    messages = {}
    for admin in await db.get_main_admins():
        try:
            if photos and len(photos) > 1:
                media_group = [InputMediaPhoto(media=photo, caption=text if i == 0 else None) for i, photo in enumerate(photos)]
                message = await bot.send_media_group(chat_id=admin, media=media_group, **kwargs)
            elif videos and len(videos) > 1:
                media_group = [InputMediaVideo(media=video, caption=text if i == 0 else None) for i, video in enumerate(videos)]
                message = await bot.send_media_group(chat_id=admin, media=media_group, **kwargs)
            elif documents and len(documents) > 1:
                media_group = [InputMediaDocument(media=doc, caption=text if i == 0 else None) for i, doc in enumerate(documents)]
                message = await bot.send_media_group(chat_id=admin, media=media_group, **kwargs)
            elif photos:
                message = await bot.send_photo(chat_id=admin, photo=photos[0], caption=text, **kwargs)
            elif videos:
                message = await bot.send_video(chat_id=admin, video=videos[0], caption=text, **kwargs)
            elif documents:
                message = await bot.send_document(chat_id=admin, document=documents[0], caption=text, **kwargs)
            else:
                message = await bot.send_message(chat_id=admin, text=text, **kwargs)
            messages[admin] = message
        except Exception as e:
            logger.warning(f'Ошибка при отправке сообщения главному админу {admin} - {e}')
            continue
    return messages


def get_russian_edit_param(param):
    data = {'photo_id': 'фото', 'keyword': 'ключевое слово', 'filter': 'фильтр', 'cashback': 'кешбек', 'product': 'товар'}
    return data.get(param) if param in data else 'неизвестно'
