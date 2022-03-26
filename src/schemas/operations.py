from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, validator

import enums


class OperationSchema(BaseModel):
    amount: int
    operation_type: enums.OperationType
    description: str
    user_id: int

    is_approved: bool = False
    repeat_type: enums.RepeatType = enums.RepeatType.NO_REPEAT
    repeat_days: Optional[List[int]] = None

    @validator('amount')
    def amount_must_be_unsigned_integer(cls, v):
        if isinstance(v, str) and not v.isdigit():
            raise ValueError('Amount must be integer')
        return abs(int(v))


class OperationCreateSchema(OperationSchema):
    """Схема создания операции"""

    pass


class OperationInDBSchema(OperationSchema):
    id: UUID
