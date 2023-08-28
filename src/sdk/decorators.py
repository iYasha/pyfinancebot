import functools
import logging
from typing import Any, Callable, Optional, Union

import sentry_sdk
from aiogram import types

from config import Environment, bot, settings
from database import database
from modules.companies.services import CompanyService
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


class SelectCompanyRequired:
    def __init__(self, func: Callable) -> None:
        self.func = func
        functools.update_wrapper(self, func)

    async def __call__(self, *args, **kwargs) -> Any:  # noqa: ANN401
        data: Optional[Union[types.Message, types.CallbackQuery]] = next(
            filter(lambda x: isinstance(x, (types.Message, types.CallbackQuery)), args),
            None,
        )
        if data is None:
            return await self.func(*args, **kwargs)

        if isinstance(data, types.Message):
            chat_id = data.chat.id
        else:
            chat_id = data.message.chat.id

        if not await self.is_company_selected(chat_id):
            return None
        return await self.func(*args, **kwargs)

    @staticmethod
    async def is_company_selected(chat_id: int) -> bool:
        company_id = settings.SELECTED_COMPANIES.get(chat_id)
        if company_id:
            return True
        companies = await CompanyService.get_my_companies(chat_id)
        if not companies:
            await bot.send_message(
                chat_id,
                text='Сначала нужно создать или вступить в компанию /companies',
            )
            return False
        elif len(companies) == 1:
            settings.SELECTED_COMPANIES[chat_id] = companies[0].id
            return True
        else:
            await bot.send_message(
                chat_id,
                text='У Вас не выбрана компания, чтобы это исправить введите /choose_company',
            )
            return False


def transaction_decorator(func: Callable) -> Callable:  # noqa: CCR001
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401
        async with database.transaction():
            return await func(*args, **kwargs)

    return wrapper
