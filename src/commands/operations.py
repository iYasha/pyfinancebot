import json
from calendar import monthrange
from datetime import datetime
from typing import Type

from commands.base import Command
from config import bot
from config import settings
from loguru import logger
from modules.operations.enums import RepeatType
from modules.operations.schemas import OperationCreate
from modules.operations.schemas import OperationImport
from modules.operations.services import OperationService

from sdk import utils


class CreateRegularOperation(Command):
    command_name = 'create_regular_operations'

    @classmethod
    async def run(cls: Type['CreateRegularOperation']) -> None:  # noqa: CCR001
        now = datetime.now()
        max_days = monthrange(now.year, now.month)[1]
        operations = await OperationService.get_regular_operations()
        for operation in operations:
            is_current_day = (
                now.day in [max_days if x == 'last' else x for x in operation.repeat_days]
                if operation.repeat_days
                else False
            )
            is_month_repeat = operation.repeat_type == RepeatType.EVERY_MONTH and is_current_day
            is_week_repeat = (
                operation.repeat_type == RepeatType.EVERY_WEEK
                and now.weekday() in operation.repeat_days
                if operation.repeat_days
                else False
            )
            is_every_day_repeat = operation.repeat_type == RepeatType.EVERY_DAY
            if is_month_repeat or is_week_repeat or is_every_day_repeat:
                operation_create = OperationCreate(
                    creator_id=operation.creator_id,
                    amount=operation.amount,
                    currency=operation.currency,
                    operation_type=operation.operation_type,
                    description=operation.description,
                    repeat_type=operation.repeat_type,
                    repeat_days=operation.repeat_days,
                    is_approved=True,
                    is_regular_operation=False,
                )
                await OperationService.create_operation(operation_create)


class SendRegularOperationNotification(Command):
    """
    TODO: Doesn't work.
    """

    command_name = 'send_regular_operations_notification'

    @classmethod
    async def run(cls: Type['SendRegularOperationNotification']) -> None:  # noqa: CCR001
        operations = await OperationService.get_regular_operations(
            is_regular_operation=False,
            has_full_amount=False,
        )
        for operation in operations:
            await bot.send_message(
                operation.creator_id,
                text=await utils.get_operation_text(operation, title='Подтвердите получение'),
                parse_mode=settings.PARSE_MODE,
                reply_markup=await utils.get_received_amount_markup(operation.id),
            )


class ImportOperations(Command):
    command_name = 'import_operations'

    @classmethod
    async def run(cls: Type['SendRegularOperationNotification']) -> None:  # noqa: CCR001
        path = 'your_path_to_json_file'
        with open(path, 'r') as f:
            operations = [
                OperationImport(
                    **x,
                )
                for x in json.loads(f.read())
            ]
            await OperationService.create_many_operations(operations)
            logger.info(f'Imported {len(operations)} operations')
