import sqlalchemy as sa

from core.database import Base

from models.base import UUIDModelMixin, AuditMixin


class Currency(
    UUIDModelMixin, AuditMixin, Base
):
    """ Базовая валюты """

    __tablename__ = "currencies"

    ccy = sa.Column(sa.String, nullable=False)
    base_ccy = sa.Column(sa.String, nullable=False)
    buy = sa.Column(sa.Float, nullable=False)
    sale = sa.Column(sa.Float, nullable=False)
