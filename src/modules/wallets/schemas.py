from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WalletSchema(BaseModel):
    name: str
    amount: Optional[int] = None
    currency: Optional[str] = None


class WalletCreateSchema(WalletSchema):
    """Схема добавления валюты"""


class WalletInDBSchema(WalletSchema):
    id: UUID
    user_id: UUID
