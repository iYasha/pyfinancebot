from modules.currencies.models import Currency
from sdk.repositories import BaseRepository


class CurrencyRepository(BaseRepository):
    model: Currency = Currency
