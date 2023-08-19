from typing import List

from asyncpg import Record
from database import database
from modules.companies.models import Company
from modules.companies.models import CompanyUser

from sdk.repositories import BaseRepository


class CompanyUserRepository(BaseRepository):
    model: CompanyUser = CompanyUser


class CompanyRepository(BaseRepository):
    model: Company = Company

    @classmethod
    async def get_my_companies(cls, chat_id: int) -> List[Record]:
        query = """
        select c.id, c.name, c.creator_id, json_group_array(json_object(
            'chat_id', u.chat_id,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'username', u.username
        )) as participants
        from companies c
        join companies_users cu on c.id = cu.company_id
        join users u on cu.chat_id = u.chat_id
        where cu.chat_id = :chat_id
        group by c.id
        """

        return await database.fetch_all(query=query, values={'chat_id': chat_id})

    @classmethod
    async def get_company_detail(cls, company_id: int) -> Record:
        query = """
        select c.id, c.name, c.creator_id, json_group_array(json_object(
            'chat_id', u.chat_id,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'username', u.username
        )) as participants
        from companies c
        join companies_users cu on c.id = cu.company_id
        join users u on cu.chat_id = u.chat_id
        where c.id = :company_id
        group by c.id
        """

        return await database.fetch_one(query=query, values={'company_id': company_id})

    @classmethod
    async def get_all_companies(cls) -> List[Record]:
        query = """
        select c.id, c.name, c.creator_id, json_group_array(json_object(
            'chat_id', u.chat_id,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'username', u.username
        )) as participants
        from companies c
        join companies_users cu on c.id = cu.company_id
        join users u on cu.chat_id = u.chat_id
        group by c.id
        """

        return await database.fetch_all(query=query)
