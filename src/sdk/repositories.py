import abc
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

import sqlalchemy as sa
from database import ModelType  # type: ignore[attr-defined]
from database import database  # type: ignore[attr-defined]
from sqlalchemy.sql import Delete
from sqlalchemy.sql import Select
from sqlalchemy.sql import Selectable
from sqlalchemy.sql.elements import BooleanClauseList

Queryable = Union[Select, Delete, BooleanClauseList, Selectable]


class BaseModifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def modify(self: 'BaseModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        raise NotImplementedError


class WhereModifier(BaseModifier):
    def __init__(self: 'WhereModifier', **kwargs) -> None:
        self.fields = kwargs

    def modify(self: 'WhereModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        return query.where(  # type: ignore[union-attr]
            sa.and_(
                *[getattr(model, key) == value for key, value in self.fields.items()],
            ),
        )

    def __repr__(self) -> str:
        return f'WhereModifier({self.fields})'

    def __eq__(self, other: 'WhereModifier') -> bool:
        if not isinstance(other, WhereModifier):
            return False
        return self.fields == other.fields


class WhereNotModifier(BaseModifier):
    def __init__(self: 'WhereNotModifier', **kwargs) -> None:
        self.fields = kwargs

    def modify(self: 'WhereNotModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        return query.where(  # type: ignore[union-attr]
            sa.and_(
                *[getattr(model, key) != value for key, value in self.fields.items()],
            ),
        )


class OrWhereModifier(BaseModifier):
    def __init__(self: 'OrWhereModifier', **kwargs) -> None:
        self.fields = kwargs

    def modify(self: 'OrWhereModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        return query.where(  # type: ignore[union-attr]
            sa.or_(
                *[getattr(model, key) == value for key, value in self.fields.items()],
            ),
        )


class InWhereModifier(BaseModifier):
    def __init__(self: 'InWhereModifier', field: str, in_: set) -> None:
        self.field = field
        self.in_ = in_

    def modify(self: 'InWhereModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        return query.where(  # type: ignore[union-attr]
            getattr(model, self.field).in_(self.in_),
        )


class ExpiredModifier(BaseModifier):
    def __init__(self, utc_now: Optional[datetime] = None) -> None:
        self.utc_now = utc_now or datetime.utcnow()

    def modify(self: 'ExpiredModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        return query.where(  # type: ignore[union-attr]
            sa.and_(
                model.end_at >= self.utc_now,
                model.start_at <= self.utc_now,
            ),
        )


class SortModifier(BaseModifier):
    def __init__(self: 'SortModifier', field: str, sort_type: str = 'asc') -> None:
        self.field = field
        self.sort_type = sa.asc if sort_type == 'asc' else sa.desc

    def modify(self: 'SortModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        return query.order_by(self.sort_type(getattr(model, self.field)))  # type: ignore[union-attr]


class SearchModifier(BaseModifier):
    def __init__(self: 'SearchModifier', **kwargs) -> None:
        self.fields = kwargs

    def modify(self: 'SearchModifier', model: Type[ModelType], query: Queryable) -> Queryable:
        return query.where(  # type: ignore[union-attr]
            sa.or_(
                *[
                    getattr(model, field).ilike(f'%{value}%')
                    for field, value in self.fields.items()
                ],
            ),
        )


class BaseRepository:
    model: Type[ModelType]

    @classmethod
    async def get(
        cls: Type['BaseRepository'],
        modifiers: List[BaseModifier],
    ) -> Optional[Dict[Any, Any]]:
        query = cls._modify_query(cls.get_base_query(), modifiers).limit(1)  # type: ignore[union-attr]
        result = await database.fetch_one(query)
        return dict(result) if result else None

    @classmethod
    async def create(
        cls: Type['BaseRepository'],
        modifiers: Optional[List[BaseModifier]] = None,
        **kwargs,
    ) -> int:
        if modifiers is None:
            modifiers = []
        # Issue: https://github.com/dropbox/sqlalchemy-stubs/issues/48
        query = cls._modify_query(sa.insert(cls.model).values(**kwargs), modifiers)  # type: ignore[arg-type]
        return await database.execute(query)

    @classmethod
    async def create_or_ignore(
        cls: Type['BaseRepository'],
        modifiers: Optional[List[BaseModifier]] = None,
        **kwargs,
    ) -> Optional[Any]:
        if modifiers is None:
            modifiers = []
        # Issue: https://github.com/dropbox/sqlalchemy-stubs/issues/48
        query = cls._modify_query(
            sa.insert(cls.model).values(**kwargs).prefix_with('OR IGNORE'),  # type: ignore[arg-type]
            modifiers,
        )
        return await database.execute(query)

    @classmethod
    async def create_many(
        cls: Type['BaseRepository'],
        values: List[Dict[str, Any]],
        modifiers: Optional[List[BaseModifier]] = None,
    ) -> Optional[Any]:
        if modifiers is None:
            modifiers = []
        # Issue: https://github.com/dropbox/sqlalchemy-stubs/issues/48
        query = cls._modify_query(sa.insert(cls.model).values(values), modifiers)  # type: ignore[arg-type]
        return await database.execute(query)

    @classmethod
    async def update(
        cls: Type['BaseRepository'],
        fields: Dict[str, Any],
        modifiers: Optional[List[BaseModifier]] = None,
        fetch_one: bool = False,
        **kwargs,
    ) -> Optional[Any]:
        if modifiers is None:
            modifiers = []
        query = cls._modify_query(
            (
                sa.update(cls.model)  # type: ignore[arg-type]
                .values(**fields)
                .where(cls.get_where_clause(**kwargs))
            ),
            modifiers,
        )
        if fetch_one:
            return await database.fetch_one(query)
        return await database.execute(query)

    @classmethod
    async def delete(
        cls: Type['BaseRepository'],
        modifiers: Optional[List[BaseModifier]] = None,
    ) -> None:
        if modifiers is None:
            modifiers = []
        query = cls._modify_query(sa.delete(cls.model), modifiers)  # type: ignore[arg-type]
        await database.execute(query)

    @classmethod
    async def all(
        cls: Type['BaseRepository'],
        modifiers: Optional[List[BaseModifier]] = None,
    ) -> List[Dict[Any, Any]]:
        if modifiers is None:
            modifiers = []
        query = cls._modify_query(cls.get_base_query(), modifiers)
        result = await database.fetch_all(query)
        return [dict(row) for row in result] if result else []

    @classmethod
    def get_base_query(
        cls: Type['BaseRepository'],
        select: Optional[Union[list, tuple]] = None,
    ) -> Select:
        if select is None:
            select = (cls.model,)
        return sa.select(select)

    @classmethod
    def get_where_clause(cls: Type['BaseRepository'], **kwargs) -> BooleanClauseList:
        return sa.and_(
            *[getattr(cls.model, key) == value for key, value in kwargs.items()],
        )

    @classmethod
    def _modify_query(
        cls: Type['BaseRepository'],
        query: Queryable,
        modifiers: List[BaseModifier],
    ) -> Queryable:
        for modifier in modifiers:
            query = modifier.modify(cls.model, query)
        return query

    @classmethod
    async def count(cls: Type['BaseRepository'], modifiers: List[BaseModifier]) -> int:
        query = cls._modify_query(
            sa.select([sa.func.count()]).select_from(cls.model),  # type: ignore[arg-type]
            modifiers,
        )
        return await database.fetch_val(query)
