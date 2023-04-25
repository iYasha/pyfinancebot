import sqlalchemy as sa
from sqlalchemy.orm import relationship

from core.database import Base

from models.base import UUIDModelMixin, AuditMixin


class User(
    UUIDModelMixin, AuditMixin, Base
):
    """ Базовая модель пользователя """

    __tablename__ = "users"

    chat_id = sa.Column(sa.Integer, unique=True, nullable=False)
    first_name = sa.Column(sa.String, nullable=True)
    last_name = sa.Column(sa.String, nullable=True)
    username = sa.Column(sa.String, nullable=True)
    is_admin = sa.Column(sa.Boolean, default=False)

    operations = relationship('Operation', uselist=True, back_populates='user')
    wallets = relationship('Wallet', uselist=True, back_populates='user')
