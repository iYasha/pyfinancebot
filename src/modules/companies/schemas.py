import json
from typing import List, Union

from aiogram.dispatcher.filters.state import State, StatesGroup
from pydantic import validator

from modules.users.schemas import User
from sdk.schemas import BaseSchema, IDSchemaMixin


class Company(IDSchemaMixin, BaseSchema):
    name: str
    creator_id: int
    participants: List[User] = []

    @validator('participants', pre=True)
    def parse_participants(cls, v: Union[str, List[User]]) -> List[User]:  # noqa: N805
        if isinstance(v, str):
            return json.loads(v)
        return v


class CompanyCreateState(StatesGroup):
    name = State()
