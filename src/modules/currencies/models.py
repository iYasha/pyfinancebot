import sqlalchemy as sa

from database import Base
from sdk.models import AuditMixin, IDModelMixin


class Currency(
    IDModelMixin,
    AuditMixin,
    Base,
):
    __tablename__ = 'currencies'

    ccy = sa.Column(sa.String, nullable=False)
    base_ccy = sa.Column(sa.String, nullable=False)
    buy = sa.Column(sa.Float, nullable=False)
    sale = sa.Column(sa.Float, nullable=False)
