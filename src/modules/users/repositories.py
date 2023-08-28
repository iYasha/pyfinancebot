from typing import Type

from modules.users.models import User
from sdk.repositories import BaseRepository


class UserRepository(BaseRepository):
    model: Type[User] = User
