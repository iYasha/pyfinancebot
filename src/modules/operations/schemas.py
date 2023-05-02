from typing import List
from typing import Optional
from typing import Type
from typing import Union

from modules.operations.enums import CurrencyEnum
from modules.operations.enums import OperationType
from modules.operations.enums import RepeatType
from pydantic import validator

from sdk.schemas import BaseSchema
from sdk.schemas import IDSchemaMixin


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
    def amount_must_be_unsigned_integer(
        cls: Type['Operation'],  # noqa: N805
        v: Union[int, str],
    ) -> int:  # noqa: N805
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
