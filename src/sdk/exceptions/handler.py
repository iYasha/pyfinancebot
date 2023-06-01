import functools
from typing import Any
from typing import Callable
from typing import Optional
from typing import Union

from aiogram import types
from asyncpg import ForeignKeyViolationError
from config import bot
from config import logger
from config import settings
from database import database
from pydantic import ValidationError


def error_handler_decorator(func: Callable) -> Callable:  # noqa: CCR001
    @functools.wraps(func)  # TODO: Refactor
    async def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401
        message: Optional[types.Message] = next(
            filter(lambda x: isinstance(x, types.Message), args),
            None,
        )
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            await bot.send_message(
                message.chat.id,
                text='\n'.join([f'{x["loc"][0]}: {x["msg"]}' for x in e.errors()]),
            )
        except ForeignKeyViolationError:  # Юзер не зарегистрирован
            await bot.send_message(
                message.chat.id,
                text='Для начала нужно зарегистрироваться /start',
            )
        except ValueError as e:
            await bot.send_message(
                message.chat.id,
                text=str(e),
            )
        except Exception:
            logger.exception('Unknown error')
            if message is None:
                return None
            await message.reply(
                text='<b>Непредвиденная ошибка!</b>\n\n'
                'Попробуйте позже или напишите в поддержку',
                parse_mode=settings.PARSE_MODE,
            )

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
    @functools.wraps(func)  # TODO: Refactor
    async def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401
        async with database.transaction():
            return await func(*args, **kwargs)

    return wrapper
