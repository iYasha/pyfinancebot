import collections
from datetime import datetime
from typing import List, Optional

import crud
from crud.base import BaseCRUD
from crud.base import BasePaginator

import sqlalchemy as sa
from core.database import database
import schemas
import models
import enums


class OperationCRUD(BaseCRUD):
    _model = models.Operation
    _model_schema = schemas.OperationInDBSchema
    _model_create_schema = schemas.OperationCreateSchema

    @classmethod
    async def get_regular_operation(
            cls,
            is_approved: bool = True,
            is_regular_operation: bool = True,
            has_full_amount: Optional[bool] = None,
    ) -> List[schemas.OperationInDBSchema]:
        query = cls.get_base_query()
        where = [
            cls._model.repeat_type != enums.RepeatType.NO_REPEAT,
            cls._model.is_approved == is_approved,
            cls._model.is_regular_operation == is_regular_operation
        ]
        if has_full_amount is not None:
            if has_full_amount:
                where.append(cls._model.amount == cls._model.received_amount)
            else:
                where.append(sa.or_(cls._model.amount != cls._model.received_amount, cls._model.received_amount == None))
        query = query.where(*where)
        results = await database.fetch_all(query)
        return [cls._get_parsed_object(obj) for obj in results]

    @classmethod
    async def get_by_user_id(
            cls,
            user_id: int,
            date_from: Optional[datetime] = None,
            date_to: Optional[datetime] = None,
            is_approved: bool = True,
            is_regular_operation: bool = False,
            has_full_amount: Optional[bool] = None,
    ) -> List[schemas.OperationInDBSchema]:
        query = cls.get_base_query()
        where = [
            cls._model.is_approved == is_approved,
            cls._model.is_regular_operation == is_regular_operation,
            cls._model.user_id == user_id
        ]
        if has_full_amount is not None:
            if has_full_amount:
                where.append(cls._model.amount == cls._model.received_amount)
            else:
                where.append(sa.or_(cls._model.amount != cls._model.received_amount, cls._model.received_amount == None))
        # If date_from is not None and date_to is not None, then we need to add it to the query
        if date_from is not None and date_to is not None:
            where.append(sa.and_(cls._model.created_at >= date_from, cls._model.created_at <= date_to))
        query = query.where(*where)
        results = await database.fetch_all(query)
        return [cls._get_parsed_object(obj) for obj in results]


    @classmethod
    async def get_most_expensive_product_group(
        cls,
        user_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 5,
    ):
        query = sa.select([sa.func.sum(cls._model.received_amount), cls._model.description, cls._model.currency])
        where = [
            cls._model.is_approved == True,
            cls._model.is_regular_operation == False,
            cls._model.user_id == user_id,
            cls._model.operation_type == enums.OperationType.EXPENSE,
        ]
        if date_from is not None and date_to is not None:
            where.append(sa.and_(cls._model.created_at >= date_from, cls._model.created_at <= date_to))
        query = query.where(*where).group_by(cls._model.description, cls._model.currency)
        results = collections.defaultdict(int)
        currencies = await crud.CurrencyCRUD.get_today()
        for result in await database.fetch_all(query):
            results[result['description']] += (result['sum_1'] * currencies[result['currency']])
        return sorted(results.items(), key=lambda x: x[1], reverse=True)[:limit]
