from typing import Type

import aiohttp
import sentry_sdk
from commands.base import Command
from modules.currencies.schemas import CurrencyCreate
from modules.currencies.services import CurrencyService


class FetchCurrency(Command):
    command_name = 'fetch_currency'
    base_url = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'

    @classmethod
    async def run(cls: Type['FetchCurrency']) -> None:  # noqa: CCR001
        async with aiohttp.ClientSession() as session:
            async with session.get(cls.base_url) as response:
                if response.status != 200:
                    sentry_sdk.capture_message(
                        f'Error fetching currency: {response.status}. {response.text}',
                    )  # noqa: G004
                    return
                data = await response.json()
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
