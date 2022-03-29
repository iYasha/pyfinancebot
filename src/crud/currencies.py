from datetime import datetime
from typing import List, Optional

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
    async def get_today(cls, ccy: enums.Currency, base_ccy: enums.Currency) -> Optional[schemas.CurrencyInDBSchema]:
        """ Получить курс валюты на сегодня """
        today = datetime.today().strftime('%Y-%m-%d')
        query = cls.get_base_query().where(
            cls._model.ccy == ccy,
            cls._model.base_ccy == base_ccy,
            cls._model.created_at == today
        )
        result = await database.fetch_one(query)
        if result is None:
            return None
        return cls._get_parsed_object(result)



