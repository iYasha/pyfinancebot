from datetime import datetime
from typing import List, Optional, Union

from crud.base import BaseCRUD
from crud.base import BasePaginator

import sqlalchemy as sa
from core.database import database
import schemas
import models
import enums


class CurrencyCRUD(BaseCRUD):
    _model = models.Currency
    _model_schema = schemas.CurrencyInDBSchema
    _model_create_schema = schemas.CurrencyCreateSchema

    @classmethod
    async def get_today(cls, ccy: Optional[enums.Currency] = None) -> Optional[Union[List[schemas.CurrencyInDBSchema], schemas.CurrencyInDBSchema]]:
        """ Получить курс валюты на сегодня """
        today = datetime.today()
        query = cls.get_base_query().where(
            cls._model.base_ccy == enums.Currency.UAH,
            sa.func.date(cls._model.created_at) == today
        )
        if ccy is not None:
            query = query.where(cls._model.ccy == ccy)
        results = await database.fetch_all(query)
        if not results:
            return None
        if ccy is not None:
            return cls._get_parsed_object(results[0])
        currencies = {x['ccy'].lower(): x['buy'] for x in results}
        currencies['uah'] = 1
        return currencies



