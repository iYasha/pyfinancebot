from datetime import datetime
from typing import Dict, List, Optional, Type, TypedDict, Union

from asyncpg import Record

from config import settings
from database import database
from modules.operations.enums import RepeatType
from modules.operations.models import Operation
from sdk.repositories import BaseRepository


class PaginatedDict(TypedDict):
    operations: List[Record]
    total: int
    page_count: int


class OperationRepository(BaseRepository):
    model: Type[Operation] = Operation

    @classmethod
    async def approve_operation(
        cls: Type['OperationRepository'],
        operation_id: int,
        category: Optional[str] = None,
    ) -> None:
        update_category = ''
        values: Dict[str, Union[str, int]] = {'operation_id': operation_id}
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
        values: Dict[str, Union[int, str]] = {'no_repeat': RepeatType.NO_REPEAT.value}
        query = """
        select o.*, round(o.amount * (case when (o.currency = 'uah') then 1 else c.buy end)) as received_amount
        from operations o
                 left join currencies c
                           on
                                       c.ccy = o.currency and
                                       c.created_at = (select max(created_at) from currencies where ccy = o.currency)
        where o.is_approved = true
          and o.is_regular_operation = true
          and o.repeat_type != :no_repeat
        """
        if company_id is not None:
            query += ' and o.company_id = :company_id'
            values['company_id'] = company_id
        return await database.fetch_all(query, values=values)

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
    ) -> PaginatedDict:
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
        data: PaginatedDict = {
            'operations': operations,
            'total': operations[0]['total'] if operations else 0,
            'page_count': 0,
        }
        data['page_count'] = (
            data['total'] // settings.PAGE_SIZE + 1
            if data['total'] % settings.PAGE_SIZE
            else data['total'] // settings.PAGE_SIZE
        )

        return data

    @classmethod
    async def get_stats_by_categories(
        cls,
        date_from: datetime,
        date_to: datetime,
        company_id: int,
    ) -> Dict[str, float]:
        query = """
        select
               o.category,
               sum(
                       case
                           when (o.operation_type = 'expense') then o.received_amount *
                                                                    (case when (o.currency = 'uah')
                                                                    then 1 else c.buy end)
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
          and o.operation_type = 'expense'
        group by o.category
        order by expense desc
        """

        values = {
            'date_from': date_from.strftime('%Y-%m-%d %H:%M:%S'),
            'date_to': date_to.strftime('%Y-%m-%d %H:%M:%S'),
            'company_id': company_id,
        }

        return {x[0]: x[1] for x in await database.fetch_all(query=query, values=values)}
