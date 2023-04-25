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

    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "app"
    DB_URI: Optional[PostgresDsn] = None

    @validator("DB_URI", pre=True)
    def assemble_db_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Union[str, PostgresDsn]:
        if isinstance(v, str):
            return v

        path = values.get("DB_NAME", "")
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=str(values.get("POSTGRES_PORT")),
            path=f"/{path}",
        )

    # Telegram
    BOT_TOKEN: Optional[str] = None


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
    +/-{amount: int} {current: длина 3 символа} {regular_period: период повторения} {description:*}
    """
    OPERATION_REGULAR_REGEX_PATTERN: str = r'^(?P<amount>[+-].[0-9]+) (?P<currency>\w{3}) (?P<repeat_time>\S.*) за (?P<description>\S.*)'

    PARSE_MODE: str = 'html'
    BOT_TOKEN: Optional[str] = EnvSettings().BOT_TOKEN
    if BOT_TOKEN is not None:
        bot = Bot(token=EnvSettings().BOT_TOKEN)
        dp = Dispatcher(bot)


class Settings(EnvSettings, HardSettings):
    pass


settings = Settings()


logger.add(settings.LOGGING_PATH + '{time:YYYY-MM-DD}.log', rotation=settings.LOGGING_ROTATION)
