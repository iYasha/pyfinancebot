from enum import Enum


class CompanyCallback(str, Enum):
    UNIQUE_PREFIX = 'co_'

    CREATE = UNIQUE_PREFIX + 'new'
    DETAIL = UNIQUE_PREFIX + 'dt'
    SELECT = UNIQUE_PREFIX + 'se'

    REMOVE_PARTICIPANT = UNIQUE_PREFIX + 'rm'
    LEAVE = UNIQUE_PREFIX + 'lv'
    DELETE = UNIQUE_PREFIX + 'dl'

    @staticmethod
    def detail(company_id: int) -> str:
        return CompanyCallback.DETAIL + f'_{company_id}'

    @staticmethod
    def select(company_id: int) -> str:
        return CompanyCallback.SELECT + f'_{company_id}'

    @staticmethod
    def remove_participant(company_id: int, chat_id: int) -> str:
        return CompanyCallback.REMOVE_PARTICIPANT + f'_{company_id}_{chat_id}'

    @classmethod
    def leave(cls, company_id: int) -> str:
        return cls.LEAVE + f'_{company_id}'

    @classmethod
    def delete(cls, company_id: int) -> str:
        return cls.DELETE + f'_{company_id}'
