from calendar import monthrange
from typing import List
import asyncio
from datetime import datetime
import aiohttp

from config import settings
from database import database
import crud
import enums
import schemas
from sdk import utils


async def on_startup() -> None:
	await database.connect()


async def on_shutdown() -> None:
	await database.disconnect()


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


async def main():
	await on_startup()

	await send_regular_payments_notification()

	await on_shutdown()


if __name__ == '__main__':
	asyncio.run(main())
