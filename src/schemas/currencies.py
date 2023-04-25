from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, validator

import enums


class CurrencySchema(BaseModel):
    ccy: str
    base_ccy: enums.Currency
    buy: float
    sale: float


class CurrencyCreateSchema(CurrencySchema):
    """Схема добавления валюты"""

    pass


class CurrencyInDBSchema(CurrencySchema):
    id: UUID
