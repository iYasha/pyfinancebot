from pydantic import BaseModel

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
