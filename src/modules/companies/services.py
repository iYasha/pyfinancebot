from typing import List

from modules.companies.repositories import CompanyRepository
from modules.companies.repositories import CompanyUserRepository
from modules.companies.schemas import Company

from sdk.repositories import WhereModifier


class CompanyService:
    repository = CompanyRepository

    @classmethod
    async def get_my_companies(cls, chat_id: int) -> List[Company]:
        return [Company(**x) for x in await cls.repository.get_my_companies(chat_id)]

    @classmethod
    async def create_company(cls, name: str, creator_id: int) -> int:
        return await cls.repository.create(name=name, creator_id=creator_id)

    @classmethod
    async def add_participant(cls, company_id: int, chat_id: int) -> None:
        is_exists = await CompanyUserRepository.get(
            [WhereModifier(company_id=company_id, chat_id=chat_id)],
        )
        if is_exists:
            raise ValueError('Вы уже состоите в этой компании!')
        await CompanyUserRepository.create(company_id=company_id, chat_id=chat_id)

    @classmethod
    async def get_company(cls, company_id: int, **kwargs) -> Company:
        company = await cls.repository.get([WhereModifier(id=company_id, **kwargs)])
        if not company:
            raise ValueError('Компания не найдена!')
        return Company(**company)

    @classmethod
    async def company_detail(cls, company_id: int) -> Company:
        company = await cls.repository.get_company_detail(company_id)
        if not company:
            raise ValueError('Компания не найдена!')
        return Company(**company)

    @classmethod
    async def delete_company(cls, company_id: int) -> None:
        await cls.repository.delete([WhereModifier(id=company_id)])

    @classmethod
    async def remove_participant(cls, company_id: int, chat_id: int) -> None:
        await CompanyUserRepository.delete([WhereModifier(company_id=company_id, chat_id=chat_id)])
