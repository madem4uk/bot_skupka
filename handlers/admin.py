from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

import sys;
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import markups as mk
import utils as u
from database import db
from other import get_logger, bot
from states import *
from states import AddProductRequestStates
from states import RejectPaymentStates


logger = get_logger(__name__)
router = Router()


@router.message(F.text == "➕ Добавить товар", u.AdminFilter())
async def add_product(message: Message, state: FSMContext):
    try:
        logger.info(f"Админ {message.chat.id} начал добавление товара")
        await message.answer('📷 Пришлите фото товара', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await state.update_data(keywords=[])
        await state.update_data(counts=[])
        await state.set_state(ProductStates.photo)
    except Exception as e:
        logger.warning(f"Ошибка при начале добавления товара: {e} - {message.chat.id}")
        
        
@router.message(StateFilter(ProductStates.photo), F.photo, u.AdminFilter())
async def handle_photo(message: Message, state: FSMContext):
    try:
        logger.info(f"Админ {message.chat.id} отправил фото товара")
        await state.update_data(photo_id=message.photo[-1].file_id)
        await message.answer(
            "Выберите площадку, на которой будет размещён товар:",
            reply_markup=mk.platform_choice_inline()
        )
        await state.set_state(ProductStates.platform)
    except Exception as e:
        logger.warning(f"Ошибка при обработке фото товара: {e} - {message.chat.id}")
        

@router.callback_query(StateFilter(ProductStates.platform), F.data.startswith("platform_"), u.AdminFilter())
async def handle_platform(call: CallbackQuery, state: FSMContext):
    try:
        platform = call.data.replace("platform_", "")
        await state.update_data(platform=platform)
        await call.message.edit_text(f"Площадка выбрана: {platform}\n\nПришлите запрос по которому покупатель должен будет найти и выкупить ваш товар.",
                                    reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await state.set_state(ProductStates.keyword)
    except Exception as e:
        logger.warning(f"Ошибка при выборе платформы: {e} - {call.message.chat.id}")
        

@router.message(StateFilter(ProductStates.keyword), F.text, u.AdminFilter())
async def handle_keyword(message: Message, state: FSMContext):
    try:
        logger.info(f"Админ {message.chat.id} отправил ключевое слово")
        data = await state.get_data()
        data['keywords'].append(message.text)
        await state.update_data(keywords=data['keywords'])
        # Логируем state после добавления ключа
        logger.warning(f"DEBUG FSM keywords: {data['keywords']}")
        await message.answer('🔑 Ключевое слово получено! Укажите количество', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await state.set_state(ProductStates.count)
    except Exception as e:
        logger.warning(f"Ошибка при обработке ключевого слова: {e} - {message.chat.id}")
        
        
@router.message(StateFilter(ProductStates.count), F.text, u.AdminFilter())
async def handle_count(message: Message, state: FSMContext):
    try:
        logger.info(f"Админ {message.chat.id} отправил количество - {message.text}")
        if message.text.isdigit() and int(message.text) > 0:
            data = await state.get_data()
            data['counts'].append(message.text)
            await state.update_data(counts=data['counts'])
            # Логируем state после добавления количества
            logger.warning(f"DEBUG FSM counts: {data['counts']}")
            await message.answer('✅ Количество получено! Хотите <b>➕ Добавить</b> ещё ключевое слово или <b>⏩ Продолжить</b>?', reply_markup=mk.add_new_keyword())
        else:
            await message.reply('Укажите нормальное количество', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
            await state.set_state(ProductStates.count)
    except Exception as e:
        logger.warning(f"Ошибка при обработке количества: {e} - {message.chat.id}")
        
        
@router.callback_query(F.data == 'add_new_keyword', u.AdminFilter())
async def add_new_keyword(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Ввод нового ключа - {call.message.chat.id}")
        await call.message.edit_text(
            text='✍️ Пришлите наименование товара',
            reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin")
        )
        await state.set_state(ProductStates.keyword)
    except Exception as e:
        logger.warning(f"Ошибка при вводе нового ключа: {e} - {call.message.chat.id}")
    

@router.callback_query(F.data == 'next_filter', u.AdminFilter())
async def next_write_filter(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Ожидание ввода фильтра - {call.message.chat.id}")
        await call.message.edit_text(
            text='✍️ Пришлите фильтр для выкупа (Название твоего бренда)',
            reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin")
        )
        await state.set_state(ProductStates.filter)
    except Exception as e:
        logger.warning(f"Ошибка при вводе фильтра: {e} - {call.message.chat.id}")
    
    
@router.message(StateFilter(ProductStates.filter), F.text, u.AdminFilter())
async def handle_filter(message: Message, state: FSMContext):
    try:
        logger.info(f"Админ {message.chat.id} отправил фильтр")
        await state.update_data(filter=message.text)
        await message.answer('🔍 Фильтр получен! Пришлите сумму кешбека', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await state.set_state(ProductStates.cashback)
    except Exception as e:
        logger.warning(f"Ошибка при обработке фильтра: {e} - {message.chat.id}")
    
    
@router.message(StateFilter(ProductStates.cashback), F.text, u.AdminFilter())
async def handle_cashback(message: Message, state: FSMContext):
    try:
        logger.info(f"Админ {message.chat.id} отправил сумму кешбека")
        await state.update_data(cashback=message.text)
        data = await state.get_data()
        # Проверка на совпадение длин
        if len(data['keywords']) != len(data['counts']):
            await message.answer('❌ Количество ключевых слов и количеств не совпадает! Проверьте ввод и попробуйте снова.', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
            return
        await db.add_product(data['photo_id'], data['keywords'], data['counts'], data['filter'], data['cashback'], message.chat.id, data.get('platform'))
        # Получаем id только что добавленного товара
        product_id = await db.get_last_product_id()

        await message.answer('💸 Сумма кешбека получена! Товар добавлен', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))

        # === РАССЫЛКА ВСЕМ ПОЛЬЗОВАТЕЛЯМ, КРОМЕ АДМИНОВ ===
        users = await db.get_users()
        admins = set(await db.get_admins())
        # Формируем текст рассылки
        product_name = data['keywords'][0] if data['keywords'] else 'Товар'
        cashback = data['cashback']
        filter_text = data['filter']
        text = f"🎉 Новый товар в каталоге!\n\n<b>{product_name}</b>\nКешбек: <b>{cashback}₽</b>\nФильтр: {filter_text}"
        photo_id = data['photo_id']
        from other import bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = None
        if product_id:
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Смотреть товар", callback_data=f"get_giveaway-{product_id}")]]
            )
        for user_id in users:
            if user_id not in admins:
                try:
                    await bot.send_photo(user_id, photo_id, caption=text, reply_markup=markup)
                except Exception:
                    pass
        # === КОНЕЦ РАССЫЛКИ ===

        # Показываем админ-меню после добавления товара
        is_main = await db.check_is_main_admin(message.chat.id)
        is_limited = await db.check_is_limited_admin(message.chat.id)
        await message.answer(
            '👑 Админ-панель',
            reply_markup=mk.admin_menu_inline(is_main, is_limited)
        )
    except Exception as e:
        logger.warning(f"Ошибка при обработке суммы кешбека: {e} - {message.chat.id}")
    finally:
        await state.clear()
        
        
@router.message(F.text == "👑 Редактирование админов", u.IsMainAdminFilter())
async def edit_admins(message: Message):
    try:
        logger.info(f'Показ опций редактирования - {message.chat.id}')
        await message.answer('Выберите нужную опцию', reply_markup=mk.edit_admins())
    except Exception as e:
        logger.warning(f'Ошибка при выборе опций редактирования: {e} - {message.chat.id}')


@router.message(F.text == "➕ Добавить", u.IsMainAdminFilter())
async def add_admin_handler(message: Message, state: FSMContext):
    try:
        logger.info(f"Главный админ {message.chat.id} начал добавление нового админа")
        await message.answer('🆔 Укажите ID телеграм аккаунта админа', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await state.set_state(AdminStates.user_id)
    except Exception as e:
        logger.warning(f"Ошибка при добавлении админа: {e} - {message.chat.id}")
        
        
@router.message(StateFilter(AdminStates.user_id), F.text, u.IsDigitFilter(), u.IsMainAdminFilter())
async def handle_admin_id(message: Message, state: FSMContext):
    try:
        logger.info(f"Главный админ {message.chat.id} указал ID нового админа")
        await message.answer('👑 Сделать админа главным?', reply_markup=mk.yes_or_no())
        await state.update_data(user_id=int(message.text))
        await state.set_state(AdminStates.is_main)
    except Exception as e:
        logger.warning(f'Ошибка при выборе уровня админа: {e} - {message.chat.id}')
        
        
@router.message(StateFilter(AdminStates.is_main), F.text, u.IsMainAdminFilter())
async def add_admin_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Добавление админа - {message.chat.id}')
        data = await state.get_data()
        await db.add_user(data['user_id'])
        await db.add_admin(data['user_id'], True if message.text == 'Да' else False)
        await message.answer('Админ успешно добавлен', reply_markup=mk.reply_empty())
    except Exception as e:
        logger.warning(f'Ошибка при добавлении админа: {e} - {message.chat.id}')
    finally:
        await state.clear()
        
        
@router.message(F.text == "➖ Удалить", u.IsMainAdminFilter())
async def delete_admin_handler(message: Message):
    try:
        logger.info(f"Главный админ {message.chat.id} начал удаление админа")
        await message.answer('🗑️ Выберите админа для удаления', reply_markup=await mk.items_pages('delete_admin', message.chat.id))
    except Exception as e:
        logger.warning(f"Ошибка при удалении админа: {e} - {message.chat.id}")
        
        
@router.callback_query(F.data.startswith('delete_admin-'), u.IsMainAdminFilter())
async def delete_admin(call: CallbackQuery):
    try:
        logger.info(f'Удаление админа - {call.message.chat.id}')
        await db.del_admin(int(call.data.split('-')[1]))
        await call.message.edit_text(
            text='🗑️ Админ успешно удалён',
            reply_markup=mk.create_one_btn_admin_back("🔙 Назад в админ-меню", "back_to_admin")
        )
    except Exception as e:
        logger.warning(f'Ошибка при удалении админа: {e} - {call.message.chat.id}')
        
        
@router.message(F.text == "🔙 Вернуться обратно", u.AdminFilter())
async def back_to_admin_menu(message: Message):
    try:
        logger.info(f"Админ {message.chat.id} вернулся в админ меню")
        await message.answer('🏠 Вы вернулись в админ меню', reply_markup=mk.admin_menu(await db.check_is_main_admin(message.chat.id)))
    except Exception as e:
        logger.warning(f"Ошибка при возвращении в админ меню: {e} - {message.chat.id}")
        
        
@router.callback_query(F.data.startswith('approve_fb-'), u.AdminFilter())
async def approve_feedback(call: CallbackQuery):
    try:
        logger.info(f"Админ {call.message.chat.id} одобрил отзыв")
        await db.set_feedbacks_status(call.data.split('-')[1], 1)
        await call.answer('✅ Отзыв успешно одобрен!')
        # Проверяем, есть ли текст в сообщении
        if call.message.text:
            await call.message.edit_text('✅ Отзыв успешно одобрен!')
        else:
            # Если сообщение содержит только фото, редактируем подпись
            await call.message.edit_caption('✅ Отзыв успешно одобрен!')
        client = await db.get_user_from_feedback(call.data.split('-')[1])
        if client:
            await bot.send_message(
                chat_id=client, 
                text='Ваш отзыв согласован администратором ✅',
                reply_markup=mk.create_one_btn("💰 Получить кешбек", "cashback")
            )
    except Exception as e:
        logger.warning(f"Ошибка при одобрении отзыва: {e} - {call.message.chat.id}")
        
        
@router.callback_query(F.data.startswith('reject_fb-'), u.AdminFilter())
async def reject_feedback(call: CallbackQuery):
    try:
        logger.info(f"Админ {call.message.chat.id} отклонил отзыв")
        feedback_id = call.data.split('-')[1]
        # Получаем user_id и product_id для удаления
        feedback = await db.get_feedback(feedback_id)
        user_id = feedback['user_id'] if feedback else None
        product_id = feedback['product_id'] if feedback else None
        await db.set_feedbacks_status(feedback_id, 2)
        await call.answer('❌ Отзыв отклонён!')
        if call.message.text:
            await call.message.edit_text('❌ Отзыв отклонён!')
        else:
            await call.message.edit_caption('❌ Отзыв отклонён!')
        # Уведомляем пользователя об отказе
        client = await db.get_user_from_feedback(feedback_id)
        if client:
            await bot.send_message(
                chat_id=client,
                text='Ваш отзыв отклонён администратором. Пожалуйста, отправьте новый корректный отзыв.',
                reply_markup=mk.create_one_btn("Согласовать отзыв", "go_to_feedback")
            )
        # Удаляем запись из feedbacks, чтобы товар снова появился для согласования
        if user_id and product_id:
            conn = await db.open()
            await conn.execute("DELETE FROM feedbacks WHERE user_id = ? AND product_id = ?", (user_id, product_id))
            await conn.commit()
    except Exception as e:
        logger.warning(f'Ошибка при отклонении отзыва: {e} - {call.message.chat.id}')
        
        
@router.message(F.text == "💳 Оплаты", u.AdminFilter())
async def payments(message: Message):
    try:
        logger.info(f"Админ {message.chat.id} запросил список оплат")
        # Проверяем, является ли админ главным
        is_main = await db.check_is_main_admin(message.chat.id)
        if is_main:
            # Главный админ видит все оплаты
            await message.answer('💳 Выберите нужную заявку', reply_markup=await mk.items_pages('get_payment', message.chat.id))
        else:
            # Ограниченный админ видит только свои оплаты
            await message.answer('💳 Выберите нужную заявку', reply_markup=await mk.items_pages('get_payment', message.chat.id, admin_id=message.chat.id))
    except Exception as e:
        logger.warning(f"Ошибка при выборе заявки на оплату: {e} - {message.chat.id}")
        
        
@router.callback_query(F.data.startswith('get_payment-'), u.AdminFilter())
async def get_payment(call: CallbackQuery):
    try:
        logger.info(f'Просмотр выплаты - {call.message.chat.id}')
        data = await db.get_payment(call.data.split('-')[1])
        if not data:
            call.message.edit_text('Данные об этой выплате отсутствуют')
            return
        try:
            user = await bot.get_chat(data.get('user_id'))
            username = f'<code>{user.id}</code>'
        except TelegramAPIError:
            username = f'<code>None - {data.get("user_id")}</code>'
        await call.message.edit_media(media=InputMediaPhoto(media=data.get('photo_id'), caption=f"<b>ID клиента:</b> {username}\n<b>Реквизиты</b>: {data.get('details')}\n<b>Сумма выплаты</b>: {data.get('cashback')} руб."), 
                                      reply_markup=mk.approve_or_reject_payment(call.data.split('-')[1]))
    except Exception as e:
        logger.warning(f'Ошибка при выдаче заявки на оплату: {e} - {call.message.chat.id}')
        
        
@router.callback_query(F.data.startswith('approve_pm-'), u.AdminFilter())
async def approve_payment(call: CallbackQuery):
    try:
        logger.info(f"Админ {call.message.chat.id} одобрил платёж")
        await db.set_payment_status(call.data.split('-')[1], 1)
        await call.message.delete()
        await call.answer('✅ Платёж успешно одобрен!')
        payment_data = await db.get_payment_data(call.data.split('-')[1])
        if payment_data:
            await bot.send_message(
                chat_id=payment_data[0], 
                text='Кешбек выплачен 🥳\nСпасибо за сотрудничество.\nОставьте положительный отзыв о нашей работе @Root_Ai', 
                disable_web_page_preview=True,
                reply_markup=mk.create_one_btn("🔙 Назад в меню", "back_to_start")
            )
            await bot.send_message(
                chat_id=call.message.chat.id,
                text='Кешбек выплачен. Спасибо за сотрудничество.'
            )
    except Exception as e:
        logger.warning(f'Ошибка при одобрении платежа: {e} - {call.message.chat.id}')
        
        
@router.callback_query(F.data.startswith('reject_pm-'), u.AdminFilter())
async def reject_payment(call: CallbackQuery, state: FSMContext):
    payment_id = call.data.split('-')[1]
    await state.update_data(payment_id=payment_id)
    await call.message.answer('✍️ Укажите причину отклонения выплаты:')
    await state.set_state(RejectPaymentStates.reason)
    await call.message.delete()
    await call.answer()

@router.message(StateFilter(RejectPaymentStates.reason), u.AdminFilter())
async def reject_payment_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get('payment_id')
    reason = message.text.strip()
    await db.set_payment_status(payment_id, 2)
    payment_data = await db.get_payment(payment_id)
    user_id = payment_data['user_id'] if payment_data else None
    await message.answer('❌ Платёж отклонён!')
    if user_id:
        await bot.send_message(
            chat_id=user_id,
            text=f'Ваша заявка на кешбек отклонена. Причина: {reason}',
            reply_markup=mk.create_one_btn('💰 Получить кешбек', 'cashback')
        )
    await state.clear()
        
        
@router.message(F.text == "✏️ Редактировать товар", u.AdminFilter())
async def payments(message: Message):
    try:
        logger.info(f'Выбор товара для редактирования - {message.chat.id}')
        is_main = await db.check_is_main_admin(message.chat.id)
        is_limited = await db.check_is_limited_admin(message.chat.id)
        
        # Ограниченные админы видят только свои товары
        admin_id = message.chat.id if is_limited else None
        
        await message.answer('📦 Выберите нужный товар', reply_markup=await mk.items_pages('edit_product', message.chat.id, admin_id=admin_id))
    except Exception as e:
        logger.warning(f'Ошибка при выборе товара для редактирования: {e} - {message.chat.id}')
        
        
@router.callback_query(F.data.startswith('edit_product-'), u.AdminFilter())
async def edit_product(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Показ товара для изменения - {call.message.chat.id}')
        product_id = call.data.split('-')[1]
        
        # Проверяем права доступа для ограниченных админов
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        if is_limited:
            # Ограниченные админы могут редактировать только свои товары
            product_admin_id = await db.get_product_admin(int(product_id))
            if product_admin_id != call.message.chat.id:
                await call.answer("❌ У вас нет прав для редактирования этого товара", show_alert=True)
                return
        
        data = await db.get_product(product_id)
        # Корректно отображаем ключевые слова и количество
        keywords = data.get('keyword', '').split(']#[') if data.get('keyword') else []
        counts = data.get('count', '').split(']#[') if data.get('count') else []
        if not counts or len(counts) != len(keywords):
            counts = ['1'] * len(keywords)
        kw_str = '\n'.join([f"<code>{k}</code> - {c}шт." for k, c in zip(keywords, counts)])
        platform = data.get('platform')
        platform_str = f"<b>Платформа</b>: <code>{platform}</code>\n" if platform else ""
        caption = f"""
{platform_str}<b>Ключевые слова</b>:\n{kw_str}
<b>Фильтр</b>: <code>{data.get('filter')}</code>
<b>Кешбек</b>: <code>{data.get('cashback')}</code> руб.
        """
        await call.message.edit_media(media=InputMediaPhoto(media=data.get('photo_id'), caption=caption), reply_markup=mk.edit_product(product_id, is_limited=is_limited))
        await state.update_data(product_id=product_id)
    except Exception as e:
        logger.warning(f'Ошибка при показе товара для изменения: {e} - {call.message.chat.id}')
        

@router.callback_query(F.data.startswith('change_keywords-'), u.AdminFilter())
async def change_keywords(call: CallbackQuery):
    try:
        logger.info(f'Изменение ключевых слов - {call.message.chat.id}')
        product_id = call.data.split('-')[1]
        
        # Проверяем права доступа для ограниченных админов
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        if is_limited:
            # Ограниченные админы могут редактировать только свои товары
            product_admin_id = await db.get_product_admin(int(product_id))
            if product_admin_id != call.message.chat.id:
                await call.answer("❌ У вас нет прав для редактирования этого товара", show_alert=True)
                return
        
        keywords = await db.get_product_keywords(product_id)
        await call.message.delete()
        await call.message.answer(f'🔰 Выберите нужное ключевое слово для удаления или добавьте новое', reply_markup=mk.edit_keywords_product(product_id, keywords))
    except Exception as e:
        logger.warning(f'Ошибка при изменении ключевых слов: {e} - {call.message.chat.id}')
        
        
@router.callback_query(F.data.startswith('add_new_keyword-'), u.AdminFilter())
async def add_new_keyword(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Ввод нового ключевого слова - {call.message.chat.id}')
        product_id = call.data.split('-')[1]
        
        # Проверяем права доступа для ограниченных админов
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        if is_limited:
            # Ограниченные админы могут редактировать только свои товары
            product_admin_id = await db.get_product_admin(int(product_id))
            if product_admin_id != call.message.chat.id:
                await call.answer("❌ У вас нет прав для редактирования этого товара", show_alert=True)
                return
        
        await call.message.edit_text(
            text=f'✍️ Введите новое ключевое слово',
            reply_markup=mk.create_one_btn_admin_back("🔙 Назад в админ-меню", "back_to_admin")
        )
        await state.update_data(product_id=product_id)
        await state.set_state(AddNewKeywordStates.keyword)
    except Exception as e:
        logger.warning(f'Ошибка при вводе ключевого слова: {e} - {call.message.chat.id}')
        

@router.message(StateFilter(AddNewKeywordStates.keyword), F.text)
async def new_keyword_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Ввод количества - {message.chat.id}')
        await state.update_data(keyword=message.text)
        await message.answer('✍️ Введите количество', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await state.set_state(AddNewKeywordStates.count)
    except Exception as e:
        logger.warning(f'Ошибка при вводе количества: {e} - {message.chat.id}')
        
        
@router.message(StateFilter(AddNewKeywordStates.count), F.text)
async def new_count_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Добавление нового ключевого слова - {message.chat.id}')
        if message.text.isdigit() and int(message.text) > 0:
            data = await state.get_data()
            await db.add_new_keyword(data['product_id'], data['keyword'], int(message.text))
            await message.answer('✅ Новое ключевое слово успешно добавлено', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        else:
            await message.reply('Укажите нормальное количество', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
            await state.set_state(AddNewKeywordStates.count)
    except Exception as e:
        logger.warning(f'Ошибка при добавлении нового ключевого слова: {e} - {message.chat.id}')


@router.callback_query(F.data.startswith('delete_keyword-'), u.AdminFilter())
async def edit_keyword(call: CallbackQuery):
    try:
        logger.info(f'Удаление ключевого слова - {call.message.chat.id}')
        product_id = call.data.split('-')[1]
        
        # Проверяем права доступа для ограниченных админов
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        if is_limited:
            # Ограниченные админы могут редактировать только свои товары
            product_admin_id = await db.get_product_admin(int(product_id))
            if product_admin_id != call.message.chat.id:
                await call.answer("❌ У вас нет прав для редактирования этого товара", show_alert=True)
                return
        
        await db.delete_keyword(product_id, call.data.split('-')[2])
        await call.message.edit_text(
            text=f'Ключевое слово успешно удалено',
            reply_markup=mk.create_one_btn_admin_back("🔙 Назад в админ-меню", "back_to_admin")
        )
    except Exception as e:
        logger.warning(f'Ошибка при удалении ключевого слова: {e} - {call.message.chat.id}')
        

@router.callback_query(F.data.startswith('edit_p_'), u.AdminFilter())
async def handle_edit_callback(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Изменение товара - {call.message.chat.id}')
        edit_type = call.data.split('-')[0].replace('edit_p_', '')
        product_id = int(call.data.split('-')[1])
        
        # Проверяем права доступа для ограниченных админов
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        if is_limited:
            # Ограниченные админы могут редактировать только свои товары
            product_admin_id = await db.get_product_admin(product_id)
            if product_admin_id != call.message.chat.id:
                await call.answer("❌ У вас нет прав для редактирования этого товара", show_alert=True)
                return
        
        await state.update_data(product_id=product_id, edit_type=edit_type)
        await call.message.delete()
        await call.message.answer(f'Отправьте новое значение для <i>{u.get_russian_edit_param(edit_type)}</i>', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await state.set_state(EditProductStates.editing)
    except Exception as e:
        logger.warning(f'Ошибка при изменении товара: {e} - {call.message.chat.id}')


@router.message(StateFilter(EditProductStates.editing), u.AdminFilter())
async def edit_message_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Изменение параметра товара - {message.chat.id}')
        data = await state.get_data()
        edit_type = data['edit_type']
        if edit_type == 'photo_id' and message.content_type == 'photo':
            new_value = message.photo[-1].file_id
        elif edit_type != 'photo_id' and message.content_type == 'text':
            new_value = message.text
        else:
            await state.set_state(EditProductStates.editing)
            return
        await db.edit_product(data['product_id'], edit_type, new_value)
        await message.answer(f'✅ Параметр <i>{u.get_russian_edit_param(edit_type)}</i> успешно изменён', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    except Exception as e:
        logger.warning(f'Ошибка при изменении {edit_type}: {e} - {message.chat.id}')
    finally:
        await state.clear()
        

@router.callback_query(F.data.startswith('delete_product-'), u.AdminFilter())
async def delete_product(call: CallbackQuery):
    try:
        logger.info(f'Удаление товара - {call.message.chat.id}')
        product_id = call.data.split('-')[1]
        
        # Проверяем права доступа для ограниченных админов
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        if is_limited:
            # Ограниченные админы могут удалять только свои товары
            product_admin_id = await db.get_product_admin(int(product_id))
            if product_admin_id != call.message.chat.id:
                await call.answer("❌ У вас нет прав для удаления этого товара", show_alert=True)
                return
        
        await db.del_product(product_id)
        await call.message.delete()
        await call.message.answer('🗑️ Товар успешно удалён', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        
        # Возвращаем в админ-меню
        await call.message.answer(
            '👑 Админ-панель',
            reply_markup=mk.admin_menu_inline(is_main, is_limited)
        )
    except Exception as e:
        logger.warning(f'Ошибка при удалении товара: {e} - {call.message.chat.id}')
        
        
@router.message(F.text == "📢 Сделать рассылку всем пользователям", u.IsMainAdminFilter())
async def mailing(message: Message, state: FSMContext):
    try:
        logger.info(f'Создание рассылки - {message.chat.id}')
        await message.answer('📨 Пришлите сообщение для рассылки\n\nВы можете отправить текст, фото, видео или документ\nЕсли передумаете, нажмите кнопку "Отмена"', reply_markup=mk.create_one_btn('❌ Отмена', 'cancel_mailing'))
        await state.set_state(MailingStates.message)
    except Exception as e:
        logger.warning(f'Ошибка при создании рассылки: {e} - {message.chat.id}')
        
        
@router.message(StateFilter(MailingStates.message), u.AdminFilter())
async def mailing_handler(message: Message, state: FSMContext):
    try:
        logger.info(f'Отправка рассылки - {message.chat.id}')
        for user_id in await db.get_users():
            try:
                await message.copy_to(chat_id=user_id)
            except TelegramAPIError:
                continue
        await message.reply('✅ Рассылка окончена', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    except Exception as e:
        logger.warning(f'Ошибка при отправки рассылки: {e} - {message.chat.id}')
    finally:
        await state.clear()
        

@router.callback_query(StateFilter(MailingStates.message), F.data == 'cancel_mailing', u.AdminFilter())
async def cancel_mailing(call: CallbackQuery, state: FSMContext):
    try:
        logger.info(f'Отмена рассылки - {call.message.chat.id}')
        await call.message.edit_text('✅ Рассылка успешно отменена', reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    except Exception as e:
        logger.warning(f'Ошибка при отмене рассылки: {e} - {call.message.chat.id}')
    finally:
        await state.clear()
        

@router.message(F.text == "⏳ Ожидает согласования", u.AdminFilter())
async def waiting_approval(message: Message):
    try:
        logger.info(f'Выбор отзыва - {message.chat.id}')
        is_main_admin = await db.check_is_main_admin(message.chat.id)
        is_limited_admin = await db.check_is_limited_admin(message.chat.id)
        
        # Ограниченные админы видят только отзывы по своим товарам
        admin_id = message.chat.id if is_limited_admin else None
        
        await message.answer(
            text='💭 Выберите отзыв', 
            reply_markup=await mk.items_pages('check_feedback', message.chat.id, admin_id=admin_id)
        )
    except Exception as e:
        logger.warning(f'Ошибка при выборе отзыва: {e} - {message.chat.id}')
        

@router.callback_query(F.data.startswith('check_feedback-'), u.AdminFilter())
async def check_feedback(call: CallbackQuery):
    try:
        logger.info(f'Просмотр отзыва - {call.message.chat.id}')
        feedback_id = call.data.split('-')[1] 
        data = await db.get_feedback(feedback_id)
        try:
            user_data = await bot.get_chat(data['user_id'])
        except TelegramAPIError:
            user_data = {'username': None}
        await call.message.delete()
        new_message = await call.message.answer_media_group(media=[InputMediaPhoto(data['feedback_photo_id'], caption=f'<b>Товар</b>: {data[await db.get_product_name(data["product_id"])]}\n<b>Ник</b>: <code>{user_data.id}</code>\n<b>Текст</b>: {data["text"]}\n<b>Ожидает</b>: {await db.get_feedback_waiting_days(feedback_id)} дней'), InputMediaPhoto(data['barcode_photo_id'])])
        await new_message[0].reply('Выберите действие', reply_markup=mk.approve_or_reject_feedback(feedback_id))
    except Exception as e:
        logger.warning(f'Ошибка при обработке callback: {e} - {call.message.chat.id}')

# --- Inline admin panel handlers ---
from aiogram.types import CallbackQuery

class AdminsStates(StatesGroup):
    add = State()
    delete = State()
    set_main = State()

class PaymentSettingsStates(StatesGroup):
    requisites = State()
    amount = State()

@router.callback_query(F.data == "admin_add_product", u.AdminFilter())
async def cb_add_product(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        '📷 Пришлите фото товара',
        reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin")
    )
    await state.update_data(keywords=[])
    await state.update_data(counts=[])
    await state.set_state(ProductStates.photo)
    await call.answer()

@router.callback_query(F.data == "admin_edit_product", u.AdminFilter())
async def cb_edit_product(call: CallbackQuery):
    try:
        logger.info(f'Выбор товара для редактирования - {call.message.chat.id}')
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        
        # Ограниченные админы видят только свои товары
        admin_id = call.message.chat.id if is_limited else None
        
        await call.message.edit_text('📦 Выберите нужный товар', reply_markup=await mk.items_pages('edit_product', call.message.chat.id, admin_id=admin_id))
    except Exception as e:
        logger.warning(f'Ошибка при выборе товара для редактирования: {e} - {call.message.chat.id}')
    await call.answer()

@router.callback_query(F.data == "admin_payments", u.AdminFilter())
async def cb_payments(call: CallbackQuery):
    try:
        logger.info(f"Админ {call.message.chat.id} запросил список оплат через inline меню")
        is_main_admin = await db.check_is_main_admin(call.message.chat.id)
        is_limited_admin = await db.check_is_limited_admin(call.message.chat.id)
        
        # Ограниченные админы видят только свои оплаты
        admin_id = call.message.chat.id if is_limited_admin else None
        
        await call.message.edit_text(
            text='💳 Выберите заявку на оплату',
            reply_markup=await mk.items_pages('get_payment', call.message.chat.id, admin_id=admin_id)
        )
    except Exception as e:
        logger.warning(f"Ошибка при показе оплат: {e} - {call.message.chat.id}")


@router.callback_query(F.data == "admin_pending", u.AdminFilter())
async def cb_pending(call: CallbackQuery):
    try:
        logger.info(f"Админ {call.message.chat.id} запросил список отзывов на ожидании")
        is_main_admin = await db.check_is_main_admin(call.message.chat.id)
        is_limited_admin = await db.check_is_limited_admin(call.message.chat.id)
        
        # Ограниченные админы видят только отзывы по своим товарам
        admin_id = call.message.chat.id if is_limited_admin else None
        
        await call.message.edit_text(
            text='⏳ Выберите отзыв для проверки',
            reply_markup=await mk.items_pages('check_feedback', call.message.chat.id, admin_id=admin_id)
        )
    except Exception as e:
        logger.warning(f"Ошибка при показе отзывов на ожидании: {e} - {call.message.chat.id}")


@router.callback_query(F.data == "go_to_payments", u.AdminFilter())
async def go_to_payments_from_notification(call: CallbackQuery):
    try:
        logger.info(f"Админ {call.message.chat.id} перешел к оплатам из уведомления")
        # Проверяем, является ли админ главным
        is_main = await db.check_is_main_admin(call.message.chat.id)
        if is_main:
            # Главный админ видит все оплаты
            await call.message.edit_text('💳 Выберите нужную заявку', reply_markup=await mk.items_pages('get_payment', call.message.chat.id))
        else:
            # Ограниченный админ видит только свои оплаты
            await call.message.edit_text('💳 Выберите нужную заявку', reply_markup=await mk.items_pages('get_payment', call.message.chat.id, admin_id=call.message.chat.id))
    except Exception as e:
        logger.warning(f"Ошибка при переходе к оплатам из уведомления: {e} - {call.message.chat.id}")
    await call.answer()

@router.callback_query(F.data == "admin_mailing", u.AdminFilter())
async def cb_mailing(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('📨 Пришлите сообщение для рассылки\n\nВы можете отправить текст, фото, видео или документ\nЕсли передумаете, нажмите кнопку "Отмена"', reply_markup=mk.create_one_btn('❌ Отмена', 'cancel_mailing'))
    await state.set_state(MailingStates.message)
    await call.answer()

@router.callback_query(F.data == "admin_admins", u.AdminFilter())
async def admin_admins_menu(call: CallbackQuery, state: FSMContext):
    is_main = await db.check_is_main_admin(call.from_user.id)
    if not is_main:
        await call.answer("Только главный админ может управлять администраторами", show_alert=True)
        return
    admins = await db.get_admins()
    text = "👑 Администраторы:\n" + "\n".join([f"- <code>{a}</code>" for a in admins])
    await call.message.edit_text(text, reply_markup=mk.edit_admins())

@router.message(StateFilter(AdminsStates.add), u.AdminFilter())
async def add_admin(message: Message, state: FSMContext):
    is_main = await db.check_is_main_admin(message.from_user.id)
    if not is_main:
        await message.answer("Только главный админ может добавлять админов", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        return
    try:
        user_id = int(message.text)
        await db.add_user(user_id)
        await db.add_admin(user_id, False, True)  # ограниченный админ
        await message.answer(f"✅ Админ {user_id} добавлен с ограниченными правами", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    except Exception as e:
        await message.answer(f"Ошибка: {e}", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    finally:
        await state.clear()

@router.message(StateFilter(AdminsStates.delete), u.AdminFilter())
async def delete_admin(message: Message, state: FSMContext):
    is_main = await db.check_is_main_admin(message.from_user.id)
    if not is_main:
        await message.answer("Только главный админ может удалять админов", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        return
    try:
        user_id = int(message.text)
        await db.del_admin(user_id)
        await message.answer(f"❌ Админ {user_id} удалён", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    except Exception as e:
        await message.answer(f"Ошибка: {e}", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    finally:
        await state.clear()

@router.callback_query(F.data == "add_admin", u.AdminFilter())
async def add_admin_btn(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите user_id нового админа:", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    await state.set_state(AdminsStates.add)

@router.callback_query(F.data == "delete_admin", u.AdminFilter())
async def delete_admin_btn(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите user_id админа для удаления:", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    await state.set_state(AdminsStates.delete)

@router.callback_query(F.data == "make_main_admin", u.AdminFilter())
async def make_main_admin_btn(call: CallbackQuery, state: FSMContext):
    is_main = await db.check_is_main_admin(call.from_user.id)
    if not is_main:
        await call.answer("Только главный админ может назначать главного", show_alert=True)
        return
    await call.message.edit_text("Введите user_id админа, которого сделать главным:", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    await state.set_state(AdminsStates.set_main)

@router.message(StateFilter(AdminsStates.set_main), u.AdminFilter())
async def set_main_admin(message: Message, state: FSMContext):
    is_main = await db.check_is_main_admin(message.from_user.id)
    if not is_main:
        await message.answer("Только главный админ может назначать главного", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        return
    try:
        user_id = int(message.text)
        await db.set_main_admin(user_id)
        await message.answer(f"⭐ Админ {user_id} теперь главный!", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        
        # Отправляем обновленное админ-меню новому главному админу
        try:
            is_new_main = await db.check_is_main_admin(user_id)
            is_new_limited = await db.check_is_limited_admin(user_id)
            await bot.send_message(
                chat_id=user_id,
                text="👑 Админ-панель (обновлена)",
                reply_markup=mk.admin_menu_inline(is_new_main, is_new_limited)
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить обновленное меню новому главному админу {user_id}: {e}")
            
    except Exception as e:
        await message.answer(f"Ошибка: {e}", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    finally:
        await state.clear()

@router.callback_query(F.data == "admin_payment_settings", u.AdminFilter())
async def admin_payment_settings(call: CallbackQuery, state: FSMContext):
    is_main = await db.check_is_main_admin(call.from_user.id)
    if not is_main:
        await call.answer("Только главный админ может менять реквизиты", show_alert=True)
        return
    settings = await db.get_payment_settings()
    text = f"Текущие реквизиты для оплаты:\n<code>{settings['requisites']}</code>\n\nСумма по умолчанию: <b>{settings['amount']}₽</b>\n\nОтправьте новые реквизиты (или оставьте как есть):"
    await call.message.edit_text(text, reply_markup=mk.create_one_btn("🔙 В меню", "back_to_start"))
    await state.set_state(PaymentSettingsStates.requisites)

@router.message(StateFilter(PaymentSettingsStates.requisites), u.AdminFilter())
async def set_payment_requisites(message: Message, state: FSMContext):
    await state.update_data(requisites=message.text)
    await message.answer("Теперь отправьте сумму по умолчанию (только число):")
    await state.set_state(PaymentSettingsStates.amount)

@router.message(StateFilter(PaymentSettingsStates.amount), u.AdminFilter())
async def set_payment_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только число!")
        return
    data = await state.get_data()
    await db.set_payment_settings(data['requisites'], int(message.text))
    await message.answer(f"Реквизиты и сумма обновлены!\n\nРеквизиты: <code>{data['requisites']}</code>\nСумма: <b>{message.text}₽</b>", reply_markup=mk.admin_menu_inline(True, False))
    await state.clear()

@router.callback_query(F.data == "back_to_start")
async def cb_back_to_start(call: CallbackQuery):
    try:
        # Проверяем, есть ли текст в сообщении
        if call.message.text:
            await call.message.edit_text(
                "Главное меню:", 
                reply_markup=mk.main_menu_inline_dynamic(call.message.chat.id)
            )
        else:
            # Если сообщение содержит только медиа, отправляем новое сообщение
            await call.message.answer(
                "Главное меню:", 
                reply_markup=mk.main_menu_inline_dynamic(call.message.chat.id)
            )
            await call.message.delete()
    except Exception as e:
        logger.warning(f"Ошибка при возврате в главное меню: {e} - {call.from_user.id}")
        # В случае ошибки отправляем новое сообщение
        await call.message.answer(
            "Главное меню:", 
            reply_markup=mk.main_menu_inline_dynamic(call.message.chat.id)
        )
        await call.message.delete()
    await call.answer()

@router.callback_query(F.data == "back_to_admin")
async def cb_back_to_admin(call: CallbackQuery):
    try:
        is_main = await db.check_is_main_admin(call.from_user.id)
        is_limited = await db.check_is_limited_admin(call.from_user.id)
        
        # Проверяем, есть ли текст в сообщении
        if call.message.text:
            await call.message.edit_text("Выберите действие", reply_markup=mk.admin_menu_inline(is_main, is_limited))
        else:
            # Если сообщение содержит только медиа, отправляем новое сообщение
            await call.message.answer("Выберите действие", reply_markup=mk.admin_menu_inline(is_main, is_limited))
            await call.message.delete()
    except Exception as e:
        logger.warning(f"Ошибка при возврате в админ-меню: {e} - {call.from_user.id}")
        # В случае ошибки отправляем новое сообщение
        is_main = await db.check_is_main_admin(call.from_user.id)
        is_limited = await db.check_is_limited_admin(call.from_user.id)
        await call.message.answer("Выберите действие", reply_markup=mk.admin_menu_inline(is_main, is_limited))
        await call.message.delete()
    await call.answer()

@router.callback_query(F.data.startswith("approve_product_request-"))
async def approve_product_request(call: CallbackQuery, state: FSMContext = None):
    request_id = int(call.data.split("-")[1])
    try:
        req = await db.get_product_request(request_id)
        if not req:
            await call.answer("Заявка не найдена", show_alert=True)
            return
        user_id = req[1]
        await db.approve_product_request(request_id)
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"✅ Заявка #{request_id} одобрена!\nПользователь <code>{user_id}</code> уведомлён.", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        # Уведомляем пользователя — показать реквизиты для оплаты и кнопку "Я оплатил"
        await bot.send_message(
            user_id,
            "Ваша заявка на размещение товара одобрена!\n\nРеквизиты для оплаты: ...\nПосле оплаты нажмите кнопку ниже.",
            reply_markup=mk.paid_button()
        )
        # Переводим пользователя в состояние ожидания оплаты-кнопки
        if state:
            await state.set_state(AddProductRequestStates.waiting_payment_button)
    except Exception as e:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer("❌ Произошла ошибка", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))

@router.callback_query(F.data.startswith("reject_product_request-"))
async def reject_product_request(call: CallbackQuery):
    request_id = int(call.data.split("-")[1])
    try:
        req = await db.get_product_request(request_id)
        if not req:
            await call.answer("Заявка не найдена", show_alert=True)
            return
        user_id = req[1]
        await db.reject_product_request(request_id)
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"❌ Заявка #{request_id} отклонена.", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await bot.send_message(user_id, "Ваша заявка на размещение товара отклонена.", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    except Exception as e:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer("❌ Произошла ошибка", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))

@router.callback_query(F.data.startswith("approve_payment_request-"))
async def approve_payment_request(call: CallbackQuery):
    request_id = int(call.data.split("-")[1])
    try:
        req = await db.get_product_request(request_id)
        if not req:
            await call.answer("Заявка не найдена", show_alert=True)
            return
        user_id = req[1]
        # Добавляем пользователя в админы (ограниченный)
        await db.add_user(user_id)
        await db.add_admin(user_id, is_main=False, is_limited=True)
        # Переносим товар в каталог (products)
        keywords = req[5].split(']#[') if req[5] else []
        counts = req[8].split(']#[') if len(req) > 8 and req[8] else ['1'] * len(keywords)
        photo_id = req[9] if len(req) > 9 and req[9] else ''
        platform = req[10] if len(req) > 10 else None
        await db.add_product(
            photo_id=photo_id,
            keywords=keywords,
            counts=counts,
            filter=req[6],
            cashback=req[7],
            admin_id=user_id,
            platform=platform
        )
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"✅ Оплата по заявке #{request_id} подтверждена. Товар добавлен в каталог, пользователь стал админом.", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        # Отправляем пользователю админ-панель
        is_main = await db.check_is_main_admin(user_id)
        is_limited = await db.check_is_limited_admin(user_id)
        await bot.send_message(
            user_id,
            "Ваша оплата подтверждена! Ваш товар добавлен в каталог, теперь вы можете управлять им в админ-панели.",
            reply_markup=mk.admin_menu_inline(is_main, is_limited)
        )
    except Exception as e:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer("❌ Произошла ошибка при подтверждении оплаты", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))

@router.callback_query(F.data.startswith("reject_payment_request-"))
async def reject_payment_request(call: CallbackQuery):
    request_id = int(call.data.split("-")[1])
    try:
        req = await db.get_product_request(request_id)
        if not req:
            await call.answer("Заявка не найдена", show_alert=True)
            return
        user_id = req[1]
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"❌ Оплата по заявке #{request_id} отклонена.", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
        await bot.send_message(user_id, "Ваша оплата по заявке отклонена. Попробуйте ещё раз или обратитесь к администратору.", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))
    except Exception as e:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer("❌ Произошла ошибка при отклонении оплаты", reply_markup=mk.create_one_btn("🔙 Назад в админ-меню", "back_to_admin"))

@router.callback_query(F.data == "admin_toggle_free_mode", u.AdminFilter())
async def admin_toggle_free_mode(call: CallbackQuery):
    is_main = await db.check_is_main_admin(call.from_user.id)
    if not is_main:
        await call.answer("Только главный админ может менять режим оплаты", show_alert=True)
        return
    is_free = await db.get_free_mode()
    new_mode = not is_free
    await db.set_free_mode(new_mode)
    actual_mode = await db.get_free_mode()
    if actual_mode == is_free:
        await call.answer(f"Режим уже {'БЕСПЛАТНЫЙ' if is_free else 'ПЛАТНЫЙ'}")
        return
    mode_str = f"\nТекущий режим: <b>{'БЕСПЛАТНЫЙ' if actual_mode else 'ПЛАТНЫЙ'}</b>"
    try:
        await call.message.edit_text(
            f"Режим изменён. Теперь бот {'БЕСПЛАТНЫЙ' if actual_mode else 'ПЛАТНЫЙ'}." + mode_str,
            reply_markup=mk.admin_menu_inline(True, False, is_free_mode=actual_mode)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer("Режим уже такой")
        else:
            raise

@router.callback_query(F.data == "admin_panel")
async def admin_panel_inline(call: CallbackQuery):
    try:
        logger.info(f'Открытие админ панели через inline - {call.message.chat.id}')
        is_admin = await db.check_is_admin(call.message.chat.id)
        if not is_admin:
            await call.answer('❌ У вас нет доступа к админ панели', show_alert=True)
            return
        is_main = await db.check_is_main_admin(call.message.chat.id)
        is_limited = await db.check_is_limited_admin(call.message.chat.id)
        is_free = await db.get_free_mode()
        mode_str = f"\nТекущий режим: <b>{'БЕСПЛАТНЫЙ' if is_free else 'ПЛАТНЫЙ'}</b>"
        await call.message.edit_text(
            text='👑 Админ панель' + mode_str,
            reply_markup=mk.admin_menu_inline(is_main, is_limited, is_free_mode=is_free)
        )
    except Exception as e:
        logger.warning(f'Ошибка при открытии админ панели через inline: {e} - {call.message.chat.id}')
