from asyncpg import ForeignKeyViolationError
from pydantic import ValidationError

from config import bot, settings


async def validator_error_handler(exc: ValidationError, chat_id: int) -> None:
    await bot.send_message(
        chat_id,
        text='\n'.join([f'{x["loc"][0]}: {x["msg"]}' for x in exc.errors()]),
    )


async def user_not_found_handler(exc: ForeignKeyViolationError, chat_id: int) -> None:
    await bot.send_message(
        chat_id,
        text='Для начала нужно зарегистрироваться /start',
    )


async def value_error_handler(exc: ValueError, chat_id: int) -> None:
    await bot.send_message(
        chat_id,
        text=str(exc),
    )


async def unexpected_exception_handler(exc: Exception, chat_id: int) -> None:
    await bot.send_message(
        chat_id,
        text='<b>Непредвиденная ошибка!</b>\n\n' 'Попробуйте позже или напишите в поддержку',
        parse_mode=settings.PARSE_MODE,
    )
