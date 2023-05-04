from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

import sqlalchemy as sa
from asyncpg import Record
from config import settings
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
        where o.created_at between :date_from and :date_to and o.is_approved = true
        """  # noqa: E501

        values = {
            'date_from': date_from.strftime('%Y-%m-%d %H:%M:%S'),
            'date_to': date_to.strftime('%Y-%m-%d %H:%M:%S'),
        }

        result = await database.fetch_one(query=query, values=values)
        return (
            {
                'income': result['income'] or 0,
                'expense': result['expense'] or 0,
            }
            if result
            else {'income': 0, 'expense': 0}
        )

    @classmethod
    async def get_operations(
        cls: Type['OperationRepository'],
        page: int = 1,
    ) -> Dict[str, Union[List[Record], int]]:
        query = """
        select *, count(*) over () as total
        from operations o
        where o.is_approved = true
        order by o.created_at desc
        limit :limit offset :offset
        """

        values = {
            'offset': (page - 1) * settings.PAGE_SIZE,
            'limit': settings.PAGE_SIZE,
        }

        operations = await database.fetch_all(query=query, values=values)
        data = {
            'operations': operations,
            'total': operations[0]['total'] if operations else 0,
        }
        data['page_count'] = (
            data['total'] // settings.PAGE_SIZE + 1
            if data['total'] % settings.PAGE_SIZE
            else data['total'] // settings.PAGE_SIZE
        )

        return data
