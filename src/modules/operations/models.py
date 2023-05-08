import sqlalchemy as sa
from database import Base

from sdk.models import AuditMixin
from sdk.models import IDModelMixin


class Operation(
    IDModelMixin,
    AuditMixin,
    Base,
):
    """ Базовая модель пользователя """

    __tablename__ = 'operations'

    amount = sa.Column(sa.Integer, nullable=False)
    received_amount = sa.Column(sa.Integer, nullable=True)
    currency = sa.Column(sa.String, nullable=False)
    operation_type = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String, nullable=True)
    repeat_type = sa.Column(sa.String, nullable=True)
    repeat_days = sa.Column(sa.JSON, nullable=True)
    is_approved = sa.Column(sa.Boolean, default=False, nullable=False)
    is_regular_operation = sa.Column(sa.Boolean, default=False, nullable=False)
    category = sa.Column(sa.String, nullable=True)
    creator_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('users.chat_id', ondelete='CASCADE'),
        nullable=False,
    )
