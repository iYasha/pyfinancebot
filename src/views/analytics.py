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
from sdk.utils import round_amount


@settings.dp.message_handler(commands=[enums.Command.TODAY])
async def get_today_analytics(message: types.Message):
	try:
		date_from, date_to = await utils.get_current_month_period()
		now_day = datetime.datetime.now().day
		currencies = await crud.CurrencyCRUD.get_today()
		data = await crud.OperationCRUD.get_by_user_id(user_id=message.chat.id, date_from=date_from, date_to=date_to)
		most_expensive_product = next(iter(await crud.OperationCRUD.get_most_expensive_product_group(user_id=message.chat.id, date_from=date_from, date_to=date_to, limit=1)), None)
		income = sum(operation.received_amount * currencies[operation.currency.value] for operation in data if operation.operation_type == enums.OperationType.INCOME and operation.received_amount is not None)
		expense = sum(operation.received_amount * currencies[operation.currency.value] for operation in data if operation.operation_type == enums.OperationType.EXPENSE and operation.received_amount is not None)
		await message.answer(f"🟢 Доход: {round_amount(income, 2)}₴\n🔴 Расход: {round_amount(expense, 2)}₴")
		# Calculate saldo and show it
		saldo = income - expense
		await message.answer(f"💸 Баланс: {round_amount(saldo, 2)}₴")
		# Calculate a day budget and show it
		day_budget = round(saldo / (date_to.day - now_day), 2)
		await message.answer(f"💰 Дневной бюджет: {round_amount(day_budget, 2)}₴")
		if most_expensive_product is not None:
			product_name, price = most_expensive_product
			await message.answer(f'🔻 Самый большой расход: {product_name} {round_amount(price, 2)}₴')
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
