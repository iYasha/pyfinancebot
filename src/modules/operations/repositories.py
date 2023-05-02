from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

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
            cls.model.is_regular_operation == is_regular_operation,
        ]
        if has_full_amount is not None:
            if has_full_amount:
                where.append(cls.model.amount == cls.model.received_amount)
            else:
                where.append(
                    sa.or_(
                        cls.model.amount != cls.model.received_amount,
                        cls.model.received_amount == None,  # noqa: E711
                    ),
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
        return (
            dict(result)
            if result
            else {
                'income': 0,
                'expense': 0,
            }
        )
