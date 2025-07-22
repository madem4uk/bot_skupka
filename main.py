import asyncio
import logging
from os import getenv
from dotenv import load_dotenv

load_dotenv()

from aiogram import Dispatcher

from handlers.user import router as us_handler_router
from handlers.admin import router as admin_handler_router
from handlers.commands import router as cmd_handler_router
from utils import router as utils_router
from database import db
from other import get_logger, bot


dp = Dispatcher()
logger = get_logger(__name__)

dp.include_routers(cmd_handler_router, admin_handler_router, us_handler_router, utils_router)


async def on_startup(bot):
    logger.info(f'Бот запущен') 


async def on_shutdown(bot):
    logger.info('Бот остановлен')

async def main() -> None:
    try:
        logging.getLogger("aiogram.event").setLevel(logging.WARNING)
        dp.shutdown.register(on_shutdown)
        dp.startup.register(on_startup)
        await db.create_tables()
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f'Ошибка при запуске бота: {e}')


if __name__ == "__main__":
    asyncio.run(main())
    