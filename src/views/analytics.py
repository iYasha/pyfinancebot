import datetime
from calendar import calendar

from pydantic import ValidationError
from asyncpg.exceptions import ForeignKeyViolationError

from core.config import settings
from aiogram import types
import re

import crud
import schemas
import enums
from sdk import utils


@settings.dp.message_handler(commands=[enums.Command.TODAY])
async def get_today_analytics(message: types.Message):
	try:
		date_from, date_to = await utils.get_current_month_period()
		data = await crud.OperationCRUD.get_by_user_id(user_id=message.chat.id, date_from=date_from, date_to=date_to)
		income = sum(operation.received_amount for operation in data if operation.operation_type == enums.OperationType.INCOME)
		expense = sum(operation.received_amount for operation in data if operation.operation_type == enums.OperationType.EXPENSE)
		await message.answer(f"Доход: {income}\nРасход: {expense}")
		# Calculate saldo and show it
		saldo = income - expense
		await message.answer(f"Баланс: {saldo}")
		# Calculate a day budget and show it
		day_budget = saldo / date_to.day
		await message.answer(f"Дневной бюджет: {day_budget}")
		print(data)
	except ValidationError as e:
		await settings.bot.send_message(
			message.chat.id,
			text='\n'.join([f'{x["loc"][0]}: {x["msg"]}' for x in e.errors()])
		)
	except ForeignKeyViolationError:  # Юзер не зарегистрирован
		await settings.bot.send_message(
			message.chat.id,
			text='Для начала нужно зарегистрироваться /start'
		)
