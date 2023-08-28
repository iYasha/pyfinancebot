from typing import Type

from modules.currencies.models import Currency
from sdk.repositories import BaseRepository


class CurrencyRepository(BaseRepository):
    model: Type[Currency] = Currency
