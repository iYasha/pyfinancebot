from typing import Optional

from sdk.schemas import BaseSchema


class UserCreate(BaseSchema):
    """Схема создания пользователя"""

    chat_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class User(UserCreate):
    pass
