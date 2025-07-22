import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from os import getenv, path


bot = Bot(token=getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def get_logger(logger_name: str) -> logging.Logger:
    """
    Создание и настрайка логгера
    :param logger_name: Имя логгера
    :param log_type: Тип ('console' или 'file')
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    log_type = getenv('LOG_TYPE')
    if log_type == 'console':
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        handler = logging.FileHandler(filename=path.join(path.dirname(path.abspath(__file__)), 'logs.txt'), encoding='UTF-8')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
