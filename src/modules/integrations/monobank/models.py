import sqlalchemy as sa

from database import Base
from sdk.models import AuditMixin


class MonobankIntegration(
    AuditMixin,
    Base,
):
    __tablename__ = 'monobank_integrations'

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
    integration_key = sa.Column(sa.String, nullable=True)
    webhook_secret = sa.Column(sa.String, nullable=True)


class Account(
    AuditMixin,
    Base,
):
    __tablename__ = 'monobank_accounts'
    __table_args__ = (
        sa.UniqueConstraint('id', 'chat_id', 'company_id', name='uq_monobank_accounts_id_chat_id_company_id'),
    )

    id = sa.Column(sa.String, primary_key=True)
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
    name = sa.Column(sa.String, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
