from typing import List

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from core.database import Base

from models.base import UUIDModelMixin, AuditMixin


class Operation(
    UUIDModelMixin, AuditMixin, Base
):
    """ Базовая модель пользователя """

    __tablename__ = "operations"

    amount = sa.Column(sa.Integer, nullable=False)
    received_amount = sa.Column(sa.Integer, nullable=True)
    currency = sa.Column(sa.String, nullable=False)
    operation_type = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String, nullable=True)
    repeat_type = sa.Column(sa.String, nullable=True)
    repeat_days = sa.Column(JSON, nullable=True)
    is_approved = sa.Column(sa.Boolean, default=False, nullable=False)
    is_regular_operation = sa.Column(sa.Boolean, default=False, nullable=False)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.chat_id'), nullable=False)
    user = relationship("User", back_populates="operations")
