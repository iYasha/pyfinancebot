import functools
from typing import Any
from typing import Callable
from typing import Optional

from aiogram import types
from asyncpg import ForeignKeyViolationError
from config import bot
from config import logger
from config import settings
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
