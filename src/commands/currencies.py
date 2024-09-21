from typing import Type

import requests
import sentry_sdk

from commands.base import Command
from modules.currencies.schemas import CurrencyCreate
from modules.currencies.services import CurrencyService


class FetchCurrency(Command):
    command_name = 'fetch_currency'
    base_url = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'

    @classmethod
    async def run(cls: Type['FetchCurrency']) -> None:  # noqa: CCR001
        response = requests.get(cls.base_url)
        if response.status_code != 200:
            sentry_sdk.capture_message(
                f'Error fetching currency: {response.status_code}. {response.text}',
            )
        data = response.json()
        currencies = [
            CurrencyCreate(
                ccy=currency['cc'].lower(),
                base_ccy='uah',
                buy=currency['rate'],
                sale=currency['rate'],
            )
            for currency in data
        ]
        await CurrencyService.create_many(currencies)
        await CurrencyService.delete_obsolete()
