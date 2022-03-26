import datetime
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from core.database import database
from crud.base import BaseCRUD
from crud.base import BasePaginator
from pydantic import parse_obj_as

import schemas
import models


class UserCRUD(BaseCRUD):
    _model = models.User
    _model_schema = schemas.UserInDBSchema
    _model_create_schema = schemas.UserCreateSchema
    _paginator = BasePaginator

    @classmethod
    async def get_by_chat_id(
            cls,
            chat_id: int,
    ) -> schemas.UserInDBSchema:
        query = cls.get_base_query()
        query = query.where(cls._model.chat_id == chat_id)
        result = await database.fetch_one(query)
        return cls._get_parsed_object(result)

    @classmethod
    @database.transaction()
    async def create_or_get(
        cls, user_data: schemas.UserCreateSchema
    ) -> schemas.UserInDBSchema:
        user = await cls.get_by_chat_id(user_data.chat_id)
        if user is not None:
            return user
        _primary_key = cls._generate_primary_key()
        _now = datetime.datetime.now()
        values = {
            **_primary_key,
            **user_data.dict(exclude_unset=True, exclude_none=True),
            cls._model.created_at.key: _now,
        }

        query = sa.insert(cls._model).values(values).returning(*cls._model.__table__.columns)
        result = await database.fetch_one(query)
        return parse_obj_as(cls._model_schema, result)
