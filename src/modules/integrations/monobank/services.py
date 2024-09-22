import json
import random
import string
from typing import Optional
from urllib.parse import urljoin

import aiohttp
import sqlalchemy as sa

from config import bot, mcc_categories, settings
from database import database
from modules.integrations.monobank.exceptions import TooManyRequests, UnknownError
from modules.integrations.monobank.models import Account, MonobankIntegration
from modules.integrations.monobank.repositories import MonobankIntegrationRepository
from modules.integrations.monobank.schemas import ClientInfo, WebhookRequest
from modules.integrations.monobank.utils import CURRENCIES_ISO_4217
from modules.operations.enums import CurrencyEnum, IncomeCategoryEnum, OperationType
from modules.operations.schemas import OperationCreate
from modules.operations.services import OperationService
from sdk.repositories import WhereModifier
from sdk.utils import get_operation_text


class MonobankIntegrationService:
    @staticmethod
    def generate_webhook_secret() -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    @classmethod
    async def get_integration_key(cls, chat_id: int, company_id: int) -> Optional[str]:
        integration = await MonobankIntegrationRepository.get([WhereModifier(chat_id=chat_id, company_id=company_id)])
        return integration.get('integration_key') if integration else None

    @classmethod
    async def remove_integration(cls, chat_id: int, company_id: int) -> None:
        await MonobankIntegrationRepository.delete([WhereModifier(chat_id=chat_id, company_id=company_id)])

    @classmethod
    async def set_integration_key(cls, chat_id: int, company_id: int, token: str) -> str:
        """
        Set integration key for Monobank integration

        :return: webhook secret
        """
        await cls.remove_integration(chat_id, company_id)
        webhook_secret = cls.generate_webhook_secret()
        await MonobankIntegrationRepository.create(
            chat_id=chat_id,
            company_id=company_id,
            integration_key=token,
            webhook_secret=webhook_secret,
        )
        return webhook_secret

    @classmethod
    async def set_accounts(cls, chat_id: int, company_id: int, client_info: ClientInfo) -> None:
        await database.execute(
            Account.__table__.delete().where(
                (Account.chat_id == chat_id) & (Account.company_id == company_id),
            ),
        )
        accounts = []
        for account in client_info.accounts:
            if account.maskedPan:
                name = f'{account.maskedPan[0]} | {account.type} | {CURRENCIES_ISO_4217.get(str(account.currencyCode))}'
            else:
                name = f'{account.type.upper()} | {CURRENCIES_ISO_4217.get(str(account.currencyCode))}'
            accounts.append(
                {
                    'id': account.id,
                    'chat_id': chat_id,
                    'company_id': company_id,
                    'name': name,
                    'is_active': True,
                },
            )
        await database.execute(Account.__table__.insert().values(accounts))

    @classmethod
    async def get_accounts(cls, chat_id: int, company_id: int) -> list[Account]:
        query = Account.__table__.select().where(
            (Account.chat_id == chat_id) & (Account.company_id == company_id),
        )
        return [Account(**dict(account)) for account in await database.fetch_all(query)]

    @classmethod
    async def delete_accounts(cls, chat_id: int, company_id: int) -> None:
        await database.execute(
            Account.__table__.delete().where(
                (Account.chat_id == chat_id) & (Account.company_id == company_id),
            ),
        )

    @classmethod
    async def change_account_status(cls, chat_id: int, company_id: int, account_id: str) -> None:
        query = (
            sa.update(Account.__table__)
            .where(
                (Account.chat_id == chat_id) & (Account.company_id == company_id) & (Account.id == account_id),
            )
            .values(is_active=~Account.is_active)
        )
        await database.execute(query)

    @classmethod
    async def check_integration_by_secret(cls, secret: str) -> Optional[MonobankIntegration]:
        integration = await MonobankIntegrationRepository.get([WhereModifier(webhook_secret=secret)])
        return MonobankIntegration(**integration) if integration else None

    @classmethod
    async def create_operation(cls, integration: MonobankIntegration, webhook_data: WebhookRequest) -> None:
        settlement_item = webhook_data.data.statementItem
        mcc_category = mcc_categories[str(settlement_item.mcc)]
        if mcc_category['short_description'] == 'Перевод средств':
            description = f'Перевод средств {settlement_item.description}'
        else:
            description = settlement_item.description
        operation_type = OperationType.EXPENSE if settlement_item.amount < 0 else OperationType.INCOME
        if operation_type == OperationType.EXPENSE:
            category = mcc_category['category']
        else:
            category = IncomeCategoryEnum.other
        operation_create = OperationCreate(
            amount=abs(settlement_item.amount) // 100,
            received_amount=abs(settlement_item.amount) // 100,
            operation_type=operation_type,
            description=description,
            creator_id=integration.chat_id,
            currency=CurrencyEnum.UAH,  # TODO: Add currency conversion
            is_approved=True,
            category=category,
            monobank_account_id=webhook_data.data.account,
        )
        operation = await OperationService.create_operation(operation_create, company_id=integration.company_id)
        await bot.send_message(
            integration.chat_id,
            get_operation_text(operation, title='Операция успешно добавлено с помощью интеграции с Monobank'),
            parse_mode=settings.PARSE_MODE,
        )

    @classmethod
    async def get_account(cls, integration: MonobankIntegration, account_id: str) -> Optional[Account]:
        query = Account.__table__.select().where(
            (Account.chat_id == integration.chat_id)
            & (Account.company_id == integration.company_id)
            & (Account.id == account_id),
        )
        account = await database.fetch_one(query)
        return Account(**dict(account)) if account else None


class MonobankService:
    BASE_URL = 'https://api.monobank.ua'

    def __init__(self, token: str):
        self.token = token

    @property
    def headers(self) -> dict:
        return {
            'X-Token': self.token,
            'User-Agent': 'financyka-bot (https://github.com/iYasha/financyka-bot) / ivan@simantiev.com',
        }

    async def send_request(self, method: str, url: str, **kwargs) -> Optional[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, urljoin(self.BASE_URL, url), headers=self.headers, **kwargs) as response:
                content = (await response.read()).decode()
                if response.status == 200 and content:
                    return json.loads(content)
                elif response.status == 200 and not content:
                    return None
                elif response.status == 429:
                    raise TooManyRequests('Too many requests')

                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    raise UnknownError(content)
                message = data.get('errorDescription', str(data))
                raise UnknownError(message)

    async def get_client_info(self) -> ClientInfo:
        data = await self.send_request('GET', '/personal/client-info')
        return ClientInfo.model_validate(data)

    async def set_webhook(self, webhook_secret) -> None:
        webhook_url = urljoin(settings.DOMAIN, f'monobank/webhook/{webhook_secret}/')
        await self.send_request('POST', '/personal/webhook', json={'webHookUrl': webhook_url})
