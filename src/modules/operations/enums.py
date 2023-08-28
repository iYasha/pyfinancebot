from enum import Enum
from typing import Optional

from config import settings
from modules.helps.enums import Command


class OperationType(str, Enum):
    """Вид операции"""

    INCOME = 'income'
    EXPENSE = 'expense'

    @staticmethod
    def get_operation_type(amount: int) -> 'OperationType':
        return OperationType.INCOME if int(amount) >= 0 else OperationType.EXPENSE

    def get_translation(self) -> str:
        if self == OperationType.INCOME:
            return 'Приход'
        elif self == OperationType.EXPENSE:
            return 'Расход'


class RepeatType(str, Enum):
    """Регулярность платежа"""

    NO_REPEAT = 'no_repeat'
    EVERY_DAY = 'every_day'
    EVERY_WEEK = 'every_week'
    EVERY_MONTH = 'every_month'

    @staticmethod
    def repeated(repeat: str) -> 'RepeatType':
        if repeat is None:
            return RepeatType.NO_REPEAT
        return RepeatType(repeat)

    def get_translation(self) -> str:
        if self == RepeatType.NO_REPEAT:
            return 'Не повторять'
        elif self == RepeatType.EVERY_DAY:
            return 'Каждый день'
        elif self == RepeatType.EVERY_WEEK:
            return 'Каждую неделю'
        elif self == RepeatType.EVERY_MONTH:
            return 'Каждый месяц'


class OperationCreateCallback(str, Enum):
    """Вид callback при создании операции"""

    UNIQUE_PREFIX = 'op_new_'

    CORRECT = UNIQUE_PREFIX + 'yes'
    NO = UNIQUE_PREFIX + 'no'

    @staticmethod
    def correct(operation_id: int, category: str, operation_type: OperationType) -> str:
        op = '+' if operation_type == OperationType.INCOME else '-'
        return OperationCreateCallback.CORRECT + f'_{operation_id}_{op}_{category}'

    @staticmethod
    def no(operation_id: int) -> str:
        return OperationCreateCallback.NO + f'_{operation_id}'


class OperationReceivedCallback(str, Enum):
    """Вид callback при получении суммы"""

    UNIQUE_PREFIX = 'op_rec_'

    FULL = UNIQUE_PREFIX + 'yes'
    PARTIAL = UNIQUE_PREFIX + 'pr'
    NONE_RECEIVED = UNIQUE_PREFIX + 'nr'

    @staticmethod
    def full(operation_id: int) -> str:
        return OperationReceivedCallback.FULL + f'_{operation_id}'

    @staticmethod
    def partial(operation_id: int) -> str:
        return OperationReceivedCallback.PARTIAL + f'_{operation_id}'

    @staticmethod
    def none_received(operation_id: int) -> str:
        return OperationReceivedCallback.NONE_RECEIVED + f'_{operation_id}'


class BackScreenType(str, Enum):
    REGULAR = 'rg'
    ALL_OPERATIONS = 'ao'
    FUTURE = 'ft'
    TODAY = 'td'

    def get_command(self) -> Optional[str]:
        if self == BackScreenType.FUTURE:
            return Command.FUTURE
        elif self == BackScreenType.TODAY:
            return Command.TODAY
        return None


class OperationAllCallback(str, Enum):
    """Вид callback для детальной информации об операции"""

    UNIQUE_PREFIX = 'op_all_'

    DETAIL = UNIQUE_PREFIX + 'dt'
    PAGINATION = UNIQUE_PREFIX + 'pg'
    DELETE = UNIQUE_PREFIX + 'dl'

    @staticmethod
    def detail(
        operation_id: int,
        page: int,
        back_type: BackScreenType = BackScreenType.ALL_OPERATIONS,
    ) -> str:
        return OperationAllCallback.DETAIL + f'_{operation_id}_{page}_{back_type}'

    @staticmethod
    def pagination(page: int, is_regular_operation: bool) -> str:
        return OperationAllCallback.PAGINATION + f'_{page}_{int(is_regular_operation)}'

    @staticmethod
    def delete(
        operation_id: int,
        page: int,
        back_type: BackScreenType = BackScreenType.ALL_OPERATIONS,
    ) -> str:
        return OperationAllCallback.DELETE + f'_{operation_id}_{page}_{back_type}'


class CurrencyEnum(str, Enum):
    """Доступные валюты в проекте"""

    USD = 'usd'
    EUR = 'eur'
    BTC = 'btc'
    UAH = 'uah'

    @staticmethod
    def get(value: Optional[str]) -> 'CurrencyEnum':
        if value is None:
            raise ValueError('Currency is required')
        currency = value.lower().strip().replace('.', '')
        if currency == 'грн':
            currency = 'uah'
        return CurrencyEnum(currency)


class ExpenseCategoryEnum(str, Enum):
    BAD_HABITS = 'bad_habits'
    EDUCATION = 'education'
    ENTERTAINMENT = 'entertainment'
    FOOD = 'food'
    HEALTH = 'health'
    HOUSE = 'house'
    PERSONAL = 'personal'
    PET = 'pet'
    SUBSCRIPTIONS = 'subscriptions'
    VEHICLE = 'vehicle'
    RENOVATION = 'renovation'
    OTHER = 'other'

    def get_translation(self) -> str:
        return settings.EXPENSE_CATEGORIES.get(self.value, self.value.capitalize())


class IncomeCategoryEnum(str, Enum):
    SALARY = 'salary'
    other = 'other'

    def get_translation(self) -> str:
        return settings.INCOME_CATEGORIES.get(self.value, self.value.capitalize())


class CategoryCallback(str, Enum):

    UNIQUE_PREFIX = 'cat_'

    SHOW_MORE = UNIQUE_PREFIX + 'more'

    @staticmethod
    def more(operation_id: int) -> str:
        return CategoryCallback.SHOW_MORE + f'_{operation_id}'
