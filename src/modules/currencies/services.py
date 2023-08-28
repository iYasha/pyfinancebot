from typing import List, Type

from modules.currencies.repositories import CurrencyRepository
from modules.currencies.schemas import CurrencyCreate


class CurrencyService:
    repository = CurrencyRepository

    @classmethod
    async def create_many(cls: Type['CurrencyService'], currencies: List[CurrencyCreate]) -> None:
        await cls.repository.create_many([currency.dict() for currency in currencies])
