from typing import Type

import sqlalchemy as sa

from database import database
from modules.currencies.models import Currency
from sdk.repositories import BaseRepository


class CurrencyRepository(BaseRepository):
    model: Type[Currency] = Currency

    @classmethod
    async def delete_obsolete(cls):
        query = """
        DELETE FROM currencies
        WHERE (ccy, created_at) NOT IN (
            SELECT ccy, MAX(created_at)
            FROM currencies
            GROUP BY ccy
        );
        """
        await database.execute(sa.text(query))
