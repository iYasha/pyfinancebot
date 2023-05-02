from typing import Optional, List, Union, Type
from uuid import UUID
from pydantic import BaseModel, validator

from modules.operations.enums import CurrencyEnum, OperationType, RepeatType
from sdk.schemas import BaseSchema, IDSchemaMixin


class OperationBase(BaseSchema):
    amount: int
    received_amount: Optional[int] = None
    operation_type: OperationType
    description: str
    creator_id: int
    currency: CurrencyEnum

    is_approved: bool = False
    repeat_type: RepeatType = RepeatType.NO_REPEAT
    repeat_days: Optional[List[Union[int, str]]] = None
    is_regular_operation: bool = False

    @validator('amount')
    def amount_must_be_unsigned_integer(cls: Type['Operation'], v: Union[int, str]) -> int:  # noqa: N805
        if isinstance(v, str) and not v.isdigit():
            raise ValueError('Amount must be integer')
        return abs(int(v))


class OperationCreate(OperationBase):
    pass


class OperationUpdate(BaseSchema):
    amount: Optional[int] = None
    received_amount: Optional[int] = None
    operation_type: Optional[OperationType] = None
    description: Optional[str] = None


class Operation(IDSchemaMixin, OperationBase):
    pass
