from types import TracebackType
from typing import Optional
from typing import Type
from typing import Union

from asyncpg import ForeignKeyViolationError
from pydantic import ValidationError

from sdk.exceptions.handlers import unexpected_exception_handler
from sdk.exceptions.handlers import user_not_found_handler
from sdk.exceptions.handlers import validator_error_handler
from sdk.exceptions.handlers import value_error_handler

exception_handler_mapping = {
    ValidationError: validator_error_handler,
    ForeignKeyViolationError: user_not_found_handler,
    ValueError: value_error_handler,
    Exception: unexpected_exception_handler,
}
ExceptionType = Union[
    BaseException,
    tuple[
        Optional[Type[BaseException]],
        Optional[BaseException],
        Optional[TracebackType],
    ],
]


async def catch_exception(exc: ExceptionType, chat_id: Optional[int] = None) -> None:
    exc_type = type(exc)
    if exc_type in exception_handler_mapping:
        await exception_handler_mapping[type(exc)](exc, chat_id)
