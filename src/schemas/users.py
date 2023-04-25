from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class UserSchema(BaseModel):
    chat_id: int


class UserCreateSchema(UserSchema):
    """Схема создания пользователя"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class UserInDBSchema(UserCreateSchema):
    id = UUID
