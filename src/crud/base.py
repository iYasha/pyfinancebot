import uuid
from datetime import datetime
from typing import Any
from typing import Callable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import Union
from uuid import UUID

import sqlalchemy as sa
from core.database import Base
from core.database import database
from pydantic import BaseModel
from schemas.common import BaseModelType, CreateSchemaType
from schemas.common import PaginatedSchema
from schemas.common import Pagination
from sqlalchemy import func
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql import Select
from pydantic import parse_obj_as

from exceptions import ValidationError, NotFoundError


class BasePaginator:
    """ Класс пагинатор для результатов запроса """

    @classmethod
    async def get_paginated_response(
        cls, model_schemer: Callable, query: Select, pagination: Pagination
    ) -> PaginatedSchema:
        page, page_size = cls.extract_values(pagination)
        paginated_query = query.limit(page_size).offset(page * page_size)
        count = await database.fetch_val(
            sa.select([func.count()]).select_from(query.alias("original_query"))
        )
        cls.check_page(count, page, page_size)

        raw_results = await database.fetch_all(paginated_query)
        _next = cls.get_next_page(count, page, page_size)
        _prev = cls.get_prev_page(page)
        results = [model_schemer(obj) for obj in raw_results]
        return PaginatedSchema(count=count, next=_next, previous=_prev, results=results)

    @classmethod
    def extract_values(cls, pagination: Pagination) -> Tuple[int, int]:
        return pagination.page, pagination.page_size

    @classmethod
    def get_next_page(cls, count: int, page: int, page_size: int) -> Optional[int]:
        return page + 1 if count > (page + 1) * page_size else None

    @classmethod
    def get_prev_page(cls, page: int) -> Optional[int]:
        return page - 1 if page > 0 else None

    @classmethod
    def check_page(cls, count: int, page: int, page_size: int) -> None:
        if page == 0:
            return
        if page * page_size >= count:
            raise ValidationError(message="Страница не найдена")


class BaseCRUD:
    _model = Base
    _model_schema = BaseModel
    _model_create_schema = CreateSchemaType
    _paginator: Optional[BasePaginator] = None
    _ordering: Optional[Sequence[ColumnElement]] = None

    @classmethod
    def get_base_query(cls) -> Select:
        return sa.select([cls._model])

    @classmethod
    def get_insert_query(cls) -> Select:
        return sa.insert(cls._model).returning(*cls._model.__table__.columns)

    @classmethod
    def _generate_primary_key(cls) -> dict:
        return {
            cls._model.id.key: uuid.uuid4(),
        }

    @classmethod
    async def create(cls, obj_in: CreateSchemaType) -> BaseModelType:
        _primary_key = cls._generate_primary_key()
        _now = datetime.now()
        values = {
            **_primary_key,
            **obj_in.dict(exclude_unset=True, exclude_none=True),
            cls._model.created_at.key: _now,
        }

        query = sa.insert(cls._model).values(values).returning(*cls._model.__table__.columns)
        result = await database.fetch_one(query)
        return parse_obj_as(cls._model_schema, result)

    @classmethod
    async def get_list(
        cls
    ) -> Union[List[BaseModelType], PaginatedSchema]:
        query = cls.get_base_query()
        return await cls.get_results(query)

    @classmethod
    async def get_by_id(
        cls,
        obj_id: UUID,
        *,
        with_deleted: Optional[bool] = False,
    ) -> Optional[BaseModelType]:
        query = cls.get_base_query()
        if with_deleted:
            where = cls._model.id == obj_id
        else:
            where = sa.and_(cls._model.id == obj_id, cls._model.deleted_at.is_(None))
        query = query.where(where)
        result = await database.fetch_one(query)
        return cls._get_parsed_object(result)

    @classmethod
    async def get_results(
        cls,
        query: Select,
        pagination: Optional[Pagination] = None,
    ) -> Union[List[BaseModelType], PaginatedSchema]:
        if cls._paginator is not None:
            return await cls._paginator.get_paginated_response(
                cls._get_parsed_object, query, pagination
            )
        results = await database.fetch_all(query)
        return [cls._get_parsed_object(obj) for obj in results]

    @classmethod
    async def update(cls, obj_id: any, **fields):
        query = sa.update(
            cls._model,
            cls._model.id == obj_id,
            fields
        )
        await database.execute(query)

    @classmethod
    async def destroy(cls, obj_id: any):
        await database.execute(
            sa.delete(cls._model, cls._model.id == obj_id)
        )

    @classmethod
    def _get_parsed_object(cls, raw_result: Optional[Any]) -> Optional[BaseModelType]:
        if raw_result is None:
            return None
        return cls._model_schema.parse_obj(raw_result)


async def get_object_or_404(
    crud: Type[BaseCRUD], obj_id: UUID
) -> BaseModelType:
    obj = await crud.get_by_id(obj_id)
    if not obj:
        raise NotFoundError()
    return obj
