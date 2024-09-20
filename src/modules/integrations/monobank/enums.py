from enum import Enum


class MonobankCallback(str, Enum):
    UNIQUE_PREFIX = 'mono_'

    CHANGE_ACCOUNT_STATUS = UNIQUE_PREFIX + 'a:'
    DISABLE = UNIQUE_PREFIX + 'disable'

    @classmethod
    def change_account_status(cls, account_id: str) -> str:
        return f'{cls.CHANGE_ACCOUNT_STATUS}{account_id}'
