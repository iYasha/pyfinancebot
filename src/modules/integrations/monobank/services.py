import json
from typing import Optional
from urllib.parse import urljoin

import aiohttp

from modules.companies.repositories import CompanyUserRepository
from modules.integrations.monobank.exceptions import TooManyRequests, UnknownError
from modules.integrations.monobank.schemas import ClientInfo
from sdk.repositories import WhereModifier


class MonobankIntegrationService:
    @classmethod
    async def is_integrated(cls, chat_id: int, company_id: int) -> bool:
        user_in_company = await CompanyUserRepository.get([WhereModifier(chat_id=chat_id, company_id=company_id)])
        return bool(user_in_company.get('monobank_integration_key')) if user_in_company else False

    @classmethod
    async def set_integration_key(cls, chat_id: int, company_id: int, token: str) -> None:
        await CompanyUserRepository.update(
            fields={'monobank_integration_key': token},
            modifiers=[WhereModifier(chat_id=chat_id, company_id=company_id)],
        )


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
        return ClientInfo.parse_obj(data)
