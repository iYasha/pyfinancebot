from enum import Enum
from uuid import UUID


class OperationType(str, Enum):
	"""Вид операции"""

	INCOME = 'income'
	EXPENSE = 'expense'

	@staticmethod
	def get_operation_type(amount: int) -> 'OperationType':
		return OperationType.INCOME if int(amount) >= 0 else OperationType.EXPENSE

	def get_translation(self):
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

	def get_translation(self):
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
	def correct(operation_id: UUID):
		return OperationCreateCallback.CORRECT + f'_{operation_id}'

	@staticmethod
	def no(operation_id: UUID):
		return OperationCreateCallback.NO + f'_{operation_id}'


class OperationReceivedCallback(str, Enum):
	"""Вид callback при получении суммы"""

	UNIQUE_PREFIX = 'op_rec_'

	FULL = UNIQUE_PREFIX + 'yes'
	PARTIAL = UNIQUE_PREFIX + 'pr'
	NONE_RECEIVED = UNIQUE_PREFIX + 'nr'

	@staticmethod
	def full(operation_id: UUID):
		return OperationReceivedCallback.FULL + f'_{operation_id}'

	@staticmethod
	def partial(operation_id: UUID):
		return OperationReceivedCallback.PARTIAL + f'_{operation_id}'

	@staticmethod
	def none_received(operation_id: UUID):
		return OperationReceivedCallback.NONE_RECEIVED + f'_{operation_id}'


class Currency(str, Enum):
	"""Доступные валюты в проекте"""

	USD = 'usd'
	EUR = 'eur'
	BTC = 'btc'
	UAH = 'uah'

	@staticmethod
	def get(value) -> 'Currency':
		currency = value.lower().strip().replace('.', '')
		if currency == 'грн':
			currency = 'uah'
		return Currency(currency)
