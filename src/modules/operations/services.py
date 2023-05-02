import re
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from config import settings
from modules.operations.enums import CurrencyEnum
from modules.operations.enums import OperationType
from modules.operations.enums import RepeatType
from modules.operations.repositories import OperationRepository
from modules.operations.schemas import Operation
from modules.operations.schemas import OperationCreate
from modules.operations.schemas import OperationUpdate

from sdk.repositories import WhereModifier
from sdk.utils import get_operation_regularity


class OperationService:
    repository = OperationRepository

    @classmethod
    async def create_operation(
        cls: Type['OperationService'],
        operation_create: OperationCreate,
    ) -> Operation:
        values = operation_create.dict()
        operation_id = await cls.repository.create(**values)
        return Operation(
            id=operation_id,
            **values,
        )

    @classmethod
    def parse_operation(
        cls: Type['OperationService'],
        text: str,
        creator_id: int,
    ) -> Optional[OperationCreate]:
        operation_add = re.match(settings.OPERATION_ADD_REGEX_PATTERN, text)
        add_regular_operation = re.match(settings.OPERATION_REGULAR_REGEX_PATTERN, text)
        if add_regular_operation is not None:
            amount, currency, repeat_time, description = add_regular_operation.groups()
            repeat_time = get_operation_regularity(repeat_time)

            return OperationCreate(
                creator_id=creator_id,
                amount=abs(int(amount)),
                received_amount=abs(int(amount)),
                currency=CurrencyEnum.get(currency),
                operation_type=OperationType.get_operation_type(amount),
                description=description,
                repeat_type=repeat_time['type'],
                repeat_days=repeat_time['days'],
                is_regular_operation=True,
            )
        elif operation_add is not None:
            amount, currency, description = re.match(
                settings.OPERATION_ADD_REGEX_PATTERN,
                text,
            ).groups()
            amount = amount.replace(' ', '').strip()
            return OperationCreate(
                creator_id=creator_id,
                amount=abs(int(amount)),
                currency=CurrencyEnum.get(currency),
                operation_type=OperationType.get_operation_type(amount),
                description=description,
                repeat_type=RepeatType.NO_REPEAT,
            )

    @classmethod
    async def approve_operation(cls: Type['OperationService'], operation_id: int) -> None:
        await cls.repository.approve_operation(operation_id)

    @classmethod
    async def delete_operation(cls: Type['OperationService'], operation_id: int) -> None:
        await cls.repository.delete([WhereModifier(id=operation_id)])

    @classmethod
    async def get_operation(
        cls: Type['OperationService'],
        operation_id: int,
    ) -> Optional[Operation]:
        operation = await cls.repository.get([WhereModifier(id=operation_id)])
        if not operation:
            return None
        return Operation(**operation)

    @classmethod
    async def update_operation(
        cls: Type['OperationService'],
        operation_id: int,
        operation_data: OperationUpdate,
    ) -> None:
        await cls.repository.update(
            fields=operation_data.dict(exclude_unset=True),
            modifiers=[WhereModifier(id=operation_id)],
        )

    @classmethod
    async def get_regular_operations(
        cls: Type['OperationService'],
        is_approved: bool = True,
        is_regular_operation: bool = True,
        has_full_amount: Optional[bool] = None,
    ) -> List[Operation]:
        operations = await cls.repository.get_regular_operations(
            is_approved=is_approved,
            is_regular_operation=is_regular_operation,
            has_full_amount=has_full_amount,
        )
        return [Operation(**operation) for operation in operations]

    @classmethod
    async def get_stats(
        cls: Type['OperationService'],
        date_from: datetime,
        date_to: datetime,
    ) -> Dict[str, float]:
        return await cls.repository.get_stats(date_from=date_from, date_to=date_to)
