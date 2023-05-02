from modules.operations.enums import CurrencyEnum
from pydantic import BaseModel


class CurrencyBase(BaseModel):
    ccy: str
    base_ccy: CurrencyEnum
    buy: float
    sale: float


class CurrencyCreate(CurrencyBase):
    pass


class Currency(CurrencyBase):
    id: int
