from aiogram.fsm.state import StatesGroup, State

class ProductStates(StatesGroup):
    photo = State()
    platform = State()  # Новое состояние для выбора площадки (админ)
    keyword = State()
    count = State()
    filter = State()
    cashback = State()

class AdminStates(StatesGroup):
    user_id = State()
    is_main = State()
    
class RevocationFeedbackStates(StatesGroup):
    product = State()
    is_understand = State()
    text = State()
    feedback_photo_id = State()
    barcode_photo_id = State()
    
class JoinDistributionStates(StatesGroup):
    product_id = State()
    photo_id = State()
    
class GetCashbackStates(StatesGroup):
    giveaway_id = State()
    photo_id = State()
    details = State()
    
class EditProductStates(StatesGroup):
    editing = State()
    
class MailingStates(StatesGroup):
    message = State()
    
class ProblemStates(StatesGroup):
    message = State()
    
class AddNewKeywordStates(StatesGroup):
    product_id = State()
    keyword = State()
    count = State()

class AddProductPaymentStates(StatesGroup):
    agree_to_terms = State()
    payment_photo = State()

class AddProductRequestStates(StatesGroup):
    photo = State()
    platform = State()  # Новое состояние для выбора площадки
    name = State()
    count = State()
    keyword_action = State()
    filter = State()
    cashback = State()
    waiting_payment_button = State()
    waiting_payment = State()
    waiting_payment_check = State()
    done = State()

class RejectPaymentStates(StatesGroup):
    reason = State()
