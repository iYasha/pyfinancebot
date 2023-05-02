from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, validator

from modules.operations.enums import CurrencyEnum


class CurrencyBase(BaseModel):
    ccy: str
    base_ccy: CurrencyEnum
    buy: float
    sale: float


class CurrencyCreate(CurrencyBase):
    pass


class Currency(CurrencyBase):
    id: int
