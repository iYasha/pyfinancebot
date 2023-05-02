import collections
from datetime import datetime
from typing import List, Optional, Type, Mapping, Dict

import sqlalchemy as sa
from asyncpg import Record

from database import database
from modules.operations.enums import RepeatType
from modules.operations.models import Operation
from sdk.repositories import BaseRepository


class OperationRepository(BaseRepository):
    model: Operation = Operation

    @classmethod
    async def approve_operation(cls: Type['OperationRepository'], operation_id: int) -> None:
        query = """
        update operations
        set is_approved = true, received_amount = amount
        where id = :operation_id
        """

        await database.execute(query=query, values={'operation_id': operation_id})

    @classmethod
    async def get_regular_operations(
        cls: Type['OperationRepository'],
        is_approved: bool,
        is_regular_operation: bool,
        has_full_amount: Optional[bool] = None,
    ) -> List[Record]:
        query = cls.get_base_query()
        where = [
            cls.model.repeat_type != RepeatType.NO_REPEAT,
            cls.model.is_approved == is_approved,
            cls.model.is_regular_operation == is_regular_operation
        ]
        if has_full_amount is not None:
            if has_full_amount:
                where.append(cls.model.amount == cls.model.received_amount)
            else:
                where.append(
                    sa.or_(cls.model.amount != cls.model.received_amount, cls.model.received_amount == None)
                )
        return await database.fetch_all(query)

    @classmethod
    async def get_stats(
        cls: Type['OperationRepository'],
        date_from: datetime,
        date_to: datetime,
    ) -> Dict[str, float]:
        query = """
        select sum(
               case
                   when (o.operation_type = 'income') then o.received_amount *
                                                           (case when (o.currency = 'uah') then 1 else c.buy end)
                   else 0 end
                   ) as income,
               sum(
                       case
                           when (o.operation_type = 'expense') then o.received_amount *
                                                                    (case when (o.currency = 'uah') then 1 else c.buy end)
                           else 0 end
                   ) as expense
        from operations o
                 left join currencies c on c.ccy = o.currency and
                                           c.created_at = (select max(created_at) from currencies where ccy = o.currency)
        where o.created_at between :date_from and :date_to
        """  # noqa: E501

        values = {
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
        }

        result = await database.fetch_one(query=query, values=values)
        return dict(result) if result else {
            'income': 0,
            'expense': 0,
        }


# class OperationCRUD(BaseCRUD):
#     _model = models.Operation
#     _model_schema = schemas.OperationInDBSchema
#     _model_create_schema = schemas.OperationCreateSchema
#
#     @classmethod
#     async def get_regular_operation(
#             cls,
#             is_approved: bool = True,
#             is_regular_operation: bool = True,
#             has_full_amount: Optional[bool] = None,
#     ) -> List[schemas.OperationInDBSchema]:
#         query = cls.get_base_query()
#         where = [
#             cls._model.repeat_type != enums.RepeatType.NO_REPEAT,
#             cls._model.is_approved == is_approved,
#             cls._model.is_regular_operation == is_regular_operation
#         ]
#         if has_full_amount is not None:
#             if has_full_amount:
#                 where.append(cls._model.amount == cls._model.received_amount)
#             else:
#                 where.append(sa.or_(cls._model.amount != cls._model.received_amount, cls._model.received_amount == None))
#         query = query.where(*where)
#         results = await database.fetch_all(query)
#         return [cls._get_parsed_object(obj) for obj in results]
#
#     @classmethod
#     async def get_by_user_id(
#             cls,
#             user_id: int,
#             date_from: Optional[datetime] = None,
#             date_to: Optional[datetime] = None,
#             is_approved: bool = True,
#             is_regular_operation: bool = False,
#             has_full_amount: Optional[bool] = None,
#     ) -> List[schemas.OperationInDBSchema]:
#         query = cls.get_base_query()
#         where = [
#             cls._model.is_approved == is_approved,
#             cls._model.is_regular_operation == is_regular_operation,
#         ]
#         if has_full_amount is not None:
#             if has_full_amount:
#                 where.append(cls._model.amount == cls._model.received_amount)
#             else:
#                 where.append(sa.or_(cls._model.amount != cls._model.received_amount, cls._model.received_amount == None))
#         # If date_from is not None and date_to is not None, then we need to add it to the query
#         if date_from is not None and date_to is not None:
#             where.append(sa.and_(cls._model.created_at >= date_from, cls._model.created_at <= date_to))
#         query = query.where(*where)
#         results = await database.fetch_all(query)
#         return [cls._get_parsed_object(obj) for obj in results]
#
#
#     @classmethod
#     async def get_most_expensive_product_group(
#         cls,
#         user_id: int,
#         date_from: Optional[datetime] = None,
#         date_to: Optional[datetime] = None,
#         limit: int = 5,
#     ):
#         query = sa.select([sa.func.sum(cls._model.received_amount), cls._model.description, cls._model.currency])
#         where = [
#             cls._model.is_approved == True,
#             cls._model.is_regular_operation == False,
#             cls._model.user_id == user_id,
#             cls._model.operation_type == enums.OperationType.EXPENSE,
#         ]
#         if date_from is not None and date_to is not None:
#             where.append(sa.and_(cls._model.created_at >= date_from, cls._model.created_at <= date_to))
#         query = query.where(*where).group_by(cls._model.description, cls._model.currency)
#         results = collections.defaultdict(int)
#         currencies = await crud.CurrencyCRUD.get_today()
#         for result in await database.fetch_all(query):
#             results[result['description']] += (result['sum_1'] * currencies[result['currency']])
#         return sorted(results.items(), key=lambda x: x[1], reverse=True)[:limit]
