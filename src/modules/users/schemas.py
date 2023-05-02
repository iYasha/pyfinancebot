from typing import Optional
from uuid import UUID

from sdk.schemas import BaseSchema


class UserCreate(BaseSchema):
    """Схема создания пользователя"""

    chat_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
