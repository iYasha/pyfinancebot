from types import TracebackType
from typing import Optional, Type, Union

import sentry_sdk
from asyncpg import ForeignKeyViolationError
from pydantic import ValidationError

from sdk.exceptions.handlers import (
    unexpected_exception_handler,
    user_not_found_handler,
    validator_error_handler,
    value_error_handler,
)

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
    is_handled_exception = exc_type in exception_handler_mapping
    if is_handled_exception and chat_id is not None:
        await exception_handler_mapping[type(exc)](exc, chat_id)
    elif is_handled_exception and chat_id is None:
        sentry_sdk.capture_exception(exc)
