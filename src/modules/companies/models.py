import sqlalchemy as sa

from database import Base
from sdk.models import IDModelMixin


class Company(
    IDModelMixin,
    Base,
):
    """Base company model"""

    __tablename__ = 'companies'

    name = sa.Column(
        sa.String(255),
        nullable=False,
    )
    creator_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('users.chat_id', ondelete='CASCADE'),
        nullable=False,
    )


class CompanyUser(Base):

    __tablename__ = 'companies_users'

    chat_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('users.chat_id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True,
    )
    company_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True,
    )
    join_date = sa.Column(
        sa.DateTime,
        nullable=False,
        server_default=sa.func.now(),
    )
    monobank_integration_key = sa.Column(sa.String, nullable=True)
