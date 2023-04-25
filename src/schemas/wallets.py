from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, validator

import enums


class WalletSchema(BaseModel):
    name: str
    amount: Optional[int] = None
    currency: Optional[str] = None


class WalletCreateSchema(WalletSchema):
    """Схема добавления валюты"""

    pass


class WalletInDBSchema(WalletSchema):
    id: UUID
    user_id: UUID
