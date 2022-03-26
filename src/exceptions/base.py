from typing import Optional, List, NamedTuple


class FieldError(NamedTuple):
    field: str
    message: str


class ValidationError(Exception):
    """Ошибка валидации."""

    DEFAULT_MESSAGE = "Ошибка валидации"

    def __init__(
            self, message: str = None, field_errors: Optional[List[FieldError]] = None
    ) -> None:
        self.message = message or self.DEFAULT_MESSAGE
        self.field_errors = field_errors


class NotFoundError(ValidationError):
    DEFAULT_MESSAGE = "Запись не найдена"
