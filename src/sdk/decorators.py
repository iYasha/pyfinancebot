import functools
import logging
from typing import Any
from typing import Callable
from typing import Optional
from typing import Union

import sentry_sdk
from aiogram import types
from config import Environment
from config import bot
from config import settings
from database import database

from sdk.exceptions.exception_handler_mapping import catch_exception


def error_handler_decorator(func: Callable) -> Callable:  # noqa: CCR001
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401
        data: Optional[Union[types.Message, types.CallbackQuery]] = next(
            filter(lambda x: isinstance(x, (types.Message, types.CallbackQuery)), args),
            None,
        )
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if settings.ENVIRONMENT == Environment.DEV:
                logging.exception(e)  # noqa: G200
            sentry_sdk.capture_exception(e)
            if data is None:
                return
            elif isinstance(data, types.Message):
                chat_id = data.chat.id
            else:
                chat_id = data.message.chat.id
            await catch_exception(e, chat_id)

    return wrapper


def select_company_required(func: Callable) -> Callable:  # noqa: CCR001
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401
        data: Optional[Union[types.Message, types.CallbackQuery]] = next(
            filter(lambda x: isinstance(x, (types.Message, types.CallbackQuery)), args),
            None,
        )
        if data is None:
            return await func(*args, **kwargs)

        if isinstance(data, types.Message):
            chat_id = data.chat.id
        else:
            chat_id = data.message.chat.id

        company_id = settings.SELECTED_COMPANIES.get(chat_id)
        if company_id is None:
            await bot.send_message(
                chat_id,
                text='Сначала нужно выбрать компанию /choose_company',
            )
            return None

        return await func(*args, **kwargs)

    return wrapper


def transaction_decorator(func: Callable) -> Callable:  # noqa: CCR001
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401
        async with database.transaction():
            return await func(*args, **kwargs)

    return wrapper
