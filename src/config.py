import os
from enum import Enum
from typing import Dict
from typing import Optional

import spacy
from aiogram import Bot
from aiogram import Dispatcher
from loguru import logger
from pydantic import BaseSettings


class Environment(str, Enum):
    PROD = 'production'
    DEV = 'dev'


class EnvSettings(BaseSettings):
    """
    Настройки из переменных окружения
    """

    PROJECT_NAME: str = 'PyFinanceBot'
    ENVIRONMENT: Optional[Environment] = Environment.PROD
    DEBUG: Optional[bool] = True
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    LOGGING_PATH: str = f'{PROJECT_ROOT}/../logs/'
    LOGGING_ROTATION: str = '500 MB'

    DB_URI: str = 'sqlite:///db.sqlite3'

    # Telegram
    BOT_TOKEN: Optional[str] = None

    # Dev settings
    TESTING: bool = False

    AI_MODELS_DIR: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


class HardSettings:
    """
    Базовые настройки
    """

    """
    Паттерн операции
    +/-{amount: int} *
    """
    OPERATION_REGEX_PATTERN: str = r'^(?P<amount>[+-].?[0-9]+) *'

    """
    Паттерн добавения операции
    +/-{amount: int} {current: длина 3 символа} {description:*}
    """
    OPERATION_ADD_REGEX_PATTERN: str = (
        r'^(?P<amount>[+-].?[0-9]+) (?P<currency>\w{3}) (?P<description>.*)'
    )

    """
    Паттерн добавления регулярных операций
    +/-{amount: int} {currency: длина 3 символа} {regular_period: период повторения} {description:*}
    """
    OPERATION_REGULAR_REGEX_PATTERN: str = r'^(?P<amount>[+-].?[0-9]+) (?P<currency>\w{3}) (?P<repeat_time>\S.*) за (?P<description>\S.*)'  # noqa: E501

    # API configuration.
    DEFAULT_DATETIME_FORMAT: str = '%Y-%m-%dT%H:%M:%S%z'

    PARSE_MODE: str = 'html'
    PAGINATION_MAX_PAGES: int = 5
    PAGE_SIZE: int = 5

    # AI Models
    CATEGORY_MODEL: str = 'category-classifier'
    OPERATION_MODEL: str = 'operation-ner'

    EXPENSE_CATEGORIES: Dict[str, str] = {
        'bad_habits': '🚬 Вредные привычки',
        'education': '📚 Образование',
        'entertainment': '🎾 Развлечения',
        'food': '🍕 Еда',
        'health': '❤️ Здоровье',
        'house': '🏠 Дом',
        'personal': '👤 Личные расходы',
        'pet': '🐶 Домашние животные',
        'subscriptions': '💰 Подписки',
        'vehicle': '🚙 Транспорт',
        'renovation': '🛠 Ремонт',
        'other': '🗃 Другое',
    }

    INCOME_CATEGORIES: Dict[str, str] = {
        'salary': '💰 Зарплата',
        'other': '🗃 Другое',
    }


class Settings(EnvSettings, HardSettings):
    pass


settings = Settings()

bot = Bot(token=settings.BOT_TOKEN)
nlp = spacy.load('ru_core_news_md')
operation_model = spacy.load(os.path.join(settings.AI_MODELS_DIR, settings.OPERATION_MODEL))
category_model = spacy.load(os.path.join(settings.AI_MODELS_DIR, settings.CATEGORY_MODEL))
dp = Dispatcher(bot)

logger.add(settings.LOGGING_PATH + '{time:YYYY-MM-DD}.log', rotation=settings.LOGGING_ROTATION)