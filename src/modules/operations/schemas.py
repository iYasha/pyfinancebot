import json
from datetime import datetime
from typing import List, Optional, Type, Union

from pydantic import validator

from modules.operations.enums import CurrencyEnum, ExpenseCategoryEnum, IncomeCategoryEnum, OperationType, RepeatType
from sdk.schemas import BaseSchema, IDSchemaMixin


class OperationBase(BaseSchema):
    amount: int
    received_amount: Optional[int] = None
    operation_type: OperationType
    category: Optional[Union[ExpenseCategoryEnum, IncomeCategoryEnum]] = None
    description: str
    creator_id: int
    currency: CurrencyEnum

    is_approved: bool = False
    repeat_type: RepeatType = RepeatType.NO_REPEAT
    repeat_days: Optional[Union[List[Union[int, str]], str]] = None
    is_regular_operation: bool = False

    @validator('repeat_days', always=True, pre=True)
    def repeat_days_must_be_list(
        cls: Type['Operation'],  # noqa: N805
        v: Optional[Union[List[Union[int, str]], str]],
    ) -> Optional[List[Union[int, str]]]:
        if isinstance(v, str) and v == 'null':
            return []
        if isinstance(v, str):
            return json.loads(v)
        return v

    @validator('amount')
    def amount_must_be_unsigned_integer(
        cls: Type['Operation'],  # noqa: N805
        v: Union[int, str],
    ) -> int:  # noqa: N805
        if isinstance(v, str) and not v.isdigit():
            raise ValueError('Amount must be integer')
        return abs(int(v))


class OperationCreate(OperationBase):
    pass


class OperationImport(OperationCreate):
    created_at: datetime


class OperationUpdate(BaseSchema):
    amount: Optional[int] = None
    received_amount: Optional[int] = None
    operation_type: Optional[OperationType] = None
    description: Optional[str] = None
    is_approved: Optional[bool] = None


class Operation(IDSchemaMixin, OperationBase):
    created_at: datetime
    company_id: int
