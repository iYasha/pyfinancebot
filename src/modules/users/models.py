import sqlalchemy as sa

from database import Base
from sdk.models import AuditMixin


class User(
    AuditMixin,
    Base,
):
    """Базовая модель пользователя"""

    __tablename__ = 'users'

    chat_id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.String, nullable=True)
    last_name = sa.Column(sa.String, nullable=True)
    username = sa.Column(sa.String, nullable=True)
