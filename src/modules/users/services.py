from typing import Type

from modules.users.repositories import UserRepository
from modules.users.schemas import UserCreate


class UserService:
    repository = UserRepository

    @classmethod
    async def create_or_ignore(cls: Type['UserService'], user_data: UserCreate) -> None:
        await cls.repository.create_or_ignore(**user_data.dict())


