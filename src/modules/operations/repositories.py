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
    async def approve_operation(
        cls: Type['OperationRepository'],
        operation_id: int,
        category: Optional[str] = None,
    ) -> None:
        update_category = ''
        values = {'operation_id': operation_id}
        if category:
            update_category = ', category = :category'
            values['category'] = category
        query = f"""
        update operations
        set is_approved = true, received_amount = amount {update_category}
        where id = :operation_id
        """

        await database.execute(
            query=query,
            values=values,
        )

    @classmethod
    async def get_regular_operations(
        cls: Type['OperationRepository'],
        company_id: Optional[int] = None,
    ) -> List[Record]:
        query = cls.get_base_query().where(
            sa.and_(
                cls.model.is_approved == True,  # noqa: E712
                cls.model.is_regular_operation == True,  # noqa: E712
                cls.model.repeat_type != RepeatType.NO_REPEAT,
            ),
        )
        if company_id is not None:
            query = query.where(cls.model.company_id == company_id)
        return await database.fetch_all(query)

    @classmethod
    async def get_stats(
        cls: Type['OperationRepository'],
        date_from: datetime,
        date_to: datetime,
        company_id: int,
    ) -> Dict[str, float]:  # TODO: Фиксировать курс на момент создания транзакции
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
                 left join currencies c on
                    c.ccy = o.currency and
                    c.created_at = (select max(created_at) from currencies where ccy = o.currency)
        where o.created_at between :date_from
            and :date_to
          and o.is_approved = true
          and o.is_regular_operation = false
          and o.company_id = :company_id
        """  # noqa: E501

        values = {
            'date_from': date_from.strftime('%Y-%m-%d %H:%M:%S'),
            'date_to': date_to.strftime('%Y-%m-%d %H:%M:%S'),
            'company_id': company_id,
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
        is_regular_operation: bool,
        company_id: int,
        page: int = 1,
    ) -> Dict[str, Union[List[Record], int]]:
        query = """
        select *, count(*) over () as total
        from operations o
        where o.is_approved = true and o.is_regular_operation = :is_regular_operation and o.company_id = :company_id
        order by o.created_at desc
        limit :limit offset :offset
        """

        values = {
            'offset': (page - 1) * settings.PAGE_SIZE,
            'limit': settings.PAGE_SIZE,
            'is_regular_operation': is_regular_operation,
            'company_id': company_id,
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
