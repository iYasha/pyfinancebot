from calendar import monthrange
from typing import List
import asyncio
from datetime import datetime
import aiohttp

from core.config import settings
from core.database import database
import crud
import enums
import schemas
from sdk import utils


async def on_startup() -> None:
	await database.connect()


async def on_shutdown() -> None:
	await database.disconnect()


async def create_regular_payments():
	now = datetime.now()
	max_days = monthrange(now.year, now.month)[1]
	operations: List[schemas.OperationInDBSchema] = await crud.OperationCRUD.get_regular_operation()
	for operation in operations:
		is_current_day = now.day in [max_days if x == 'last' else x for x in operation.repeat_days]
		is_month_repeat = operation.repeat_type == enums.RepeatType.EVERY_MONTH and is_current_day
		is_week_repeat = operation.repeat_type == enums.RepeatType.EVERY_WEEK and now.weekday() in operation.repeat_days
		is_every_day_repeat = operation.repeat_type == enums.RepeatType.EVERY_DAY
		if is_month_repeat or is_week_repeat or is_every_day_repeat:
			operation_create = schemas.OperationCreateSchema(
				user_id=operation.user_id,
				amount=operation.amount,
				currency=operation.currency,
				operation_type=operation.operation_type,
				description=operation.description,
				repeat_type=operation.repeat_type,
				repeat_days=operation.repeat_days,
				is_approved=True,
				is_regular_operation=False
			)
			await crud.OperationCRUD.create(operation_create)


async def send_regular_payments_notification():
	operations: List[schemas.OperationInDBSchema] = await crud.OperationCRUD.get_regular_operation(
		is_regular_operation=False,
		has_full_amount=False
	)
	for operation in operations:
		await settings.bot.send_message(
			operation.user_id,
			text=await utils.get_operation_text(operation, title='Подтвердите получение'),
			parse_mode=settings.PARSE_MODE,
			reply_markup=await utils.get_received_amount_markup(operation.id)
		)


async def get_currencies_rate():
	async with aiohttp.ClientSession() as session:
		async with session.get('https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json') as response:
			data = await response.json()
			for currency in data:
				currency_create = schemas.CurrencyCreateSchema(
					ccy=currency['cc'].lower(),
					base_ccy='uah',
					buy=currency['rate'],
					sale=currency['rate'],
				)
				await crud.CurrencyCRUD.create(currency_create)


async def main():
	await on_startup()

	await create_regular_payments()
	await send_regular_payments_notification()
	await get_currencies_rate()

	await on_shutdown()


if __name__ == '__main__':
	asyncio.run(main())
