import json
from calendar import monthrange
from datetime import datetime
from typing import Type

import sentry_sdk

from commands.base import Command
from config import bot, settings
from modules.operations.enums import OperationType
from modules.operations.schemas import OperationImport
from modules.operations.services import OperationService
from sdk import utils


class CreateRegularOperation(Command):
    command_name = 'create_regular_operations'

    @classmethod
    async def run(cls: Type['CreateRegularOperation']) -> None:
        now = datetime.now()
        last_month_day = monthrange(now.year, now.month)[1]
        operations = await OperationService.get_regular_operations()
        for operation in operations:
            new_operation = await OperationService.create_regular_operation(
                operation,
                now,
                last_month_day,
            )
            if new_operation:
                is_income = new_operation.operation_type == OperationType.INCOME
                await bot.send_message(
                    new_operation.creator_id,
                    text=utils.get_operation_text(
                        new_operation,
                        title='Подтвердите операцию',
                        is_regular=True,
                    ),
                    parse_mode=settings.PARSE_MODE,
                    reply_markup=await utils.get_received_amount_markup(
                        new_operation.id,
                        is_income,
                    ),
                )


class ImportOperations(Command):
    command_name = 'import_operations'

    @classmethod
    async def run(cls: Type['ImportOperations']) -> None:  # noqa: CCR001
        path = 'your_path_to_json_file'
        with open(path, 'r') as f:
            operations = [
                OperationImport(
                    **x,
                )
                for x in json.loads(f.read())
            ]
            await OperationService.create_many_operations(operations)
            sentry_sdk.capture_message(f'Imported {len(operations)} operations')
