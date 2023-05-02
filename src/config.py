import os
from loguru import logger
from pydantic import BaseSettings
from pydantic.networks import PostgresDsn
from pydantic import validator
from enum import Enum
from typing import Optional, Dict, Any, Union
from aiogram import Bot, Dispatcher


class Environment(Enum):
    PROD = "production"
    DEV = "dev"


class EnvSettings(BaseSettings):
    """
    Настройки из переменных окружения
    """

    PROJECT_NAME: str = "PyFinanceBot"
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

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


class PersonalDispatcher(Dispatcher):
    def message_handler(
        self, *custom_filters, commands=None, regexp=None, content_types=None, state=None,
        run_task=None, **kwargs
    ):
        """
        Decorator for message handler

        Examples:

        Simple commands handler:

        .. code-block:: python3

            @dp.message_handler(commands=['start', 'welcome', 'about'])
            async def cmd_handler(message: types.Message):

        Filter messages by regular expression:

        .. code-block:: python3

            @dp.message_handler(regexp='^[a-z]+-[0-9]+')
            async def msg_handler(message: types.Message):

        Filter messages by command regular expression:

        .. code-block:: python3

            @dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['item_([0-9]*)']))
            async def send_welcome(message: types.Message):

        Filter by content type:

        .. code-block:: python3

            @dp.message_handler(content_types=ContentType.PHOTO | ContentType.DOCUMENT)
            async def audio_handler(message: types.Message):

        Filter by custom function:

        .. code-block:: python3

            @dp.message_handler(lambda message: message.text and 'hello' in message.text.lower())
            async def text_handler(message: types.Message):

        Use multiple filters:

        .. code-block:: python3

            @dp.message_handler(commands=['command'], content_types=ContentType.TEXT)
            async def text_handler(message: types.Message):

        Register multiple filters set for one handler:

        .. code-block:: python3

            @dp.message_handler(commands=['command'])
            @dp.message_handler(lambda message: demojize(message.text) == ':new_moon_with_face:')
            async def text_handler(message: types.Message):

        This handler will be called if the message starts with '/command' OR is some emoji

        By default content_type is :class:`ContentType.TEXT`

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param custom_filters: list of custom filters
        :param kwargs:
        :param state:
        :param run_task: run callback in task (no wait results)
        :return: decorated function
        """

        def decorator(callback):
            self.register_message_handler(
                callback, *custom_filters,
                commands=commands, regexp=regexp, content_types=content_types,
                state=state, run_task=run_task, **kwargs
            )
            return callback

        return decorator


class HardSettings:
    """
    Базовые настройки
    """

    """
    Паттерн операции
    +/-{amount: int} *
    """
    OPERATION_REGEX_PATTERN: str = r'^(?P<amount>[+-].[0-9]+) *'

    """
    Паттерн добавения операции
    +/-{amount: int} {current: длина 3 символа} {description:*}
    """
    OPERATION_ADD_REGEX_PATTERN: str = r'^(?P<amount>[+-].[0-9]+) (?P<currency>\w{3}) (?P<description>.*)'

    """
    Паттерн добавления регулярных операций
    +/-{amount: int} {currency: длина 3 символа} {regular_period: период повторения} {description:*}
    """
    OPERATION_REGULAR_REGEX_PATTERN: str = r'^(?P<amount>[+-].[0-9]+) (?P<currency>\w{3}) (?P<repeat_time>\S.*) за (?P<description>\S.*)'

    # API configuration.
    DEFAULT_DATETIME_FORMAT: str = '%Y-%m-%dT%H:%M:%S%z'

    PARSE_MODE: str = 'html'


class Settings(EnvSettings, HardSettings):
    pass


settings = Settings()

bot = Bot(token=settings.BOT_TOKEN)
dp = PersonalDispatcher(bot)

logger.add(settings.LOGGING_PATH + '{time:YYYY-MM-DD}.log', rotation=settings.LOGGING_ROTATION)
