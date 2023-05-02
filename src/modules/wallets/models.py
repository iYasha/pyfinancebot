import sqlalchemy as sa
from sqlalchemy.orm import relationship

from database import Base

from models.base import UUIDModelMixin


class Wallet(
    UUIDModelMixin, Base
):
    """ Базовая модель кошелька пользователя """

    __tablename__ = 'wallets'

    name = sa.Column(sa.String, nullable=False)
    amount = sa.Column(sa.Integer, nullable=True)
    currency = sa.Column(sa.String, nullable=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.chat_id'), nullable=False)
    user = relationship("User", back_populates="wallets")


