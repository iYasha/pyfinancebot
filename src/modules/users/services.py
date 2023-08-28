from typing import Optional, Type

from modules.users.repositories import UserRepository
from modules.users.schemas import User, UserCreate
from sdk.repositories import WhereModifier


class UserService:
    repository = UserRepository

    @classmethod
    async def get_user(cls, chat_id: int) -> Optional[User]:
        user = await cls.repository.get([WhereModifier(chat_id=chat_id)])
        if not user:
            return None
        return User(**user)

    @classmethod
    async def create_or_ignore(cls: Type['UserService'], user_data: UserCreate) -> None:
        await cls.repository.create_or_ignore(**user_data.dict())
