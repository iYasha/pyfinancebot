import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


class UUIDModelMixin:
	id = sa.Column(UUID, primary_key=True, default=uuid.uuid4)


class SoftDeleteModelMixin:
	is_deleted = sa.Column(sa.Boolean(), default=False)


class AuditMixin:
	created_at = sa.Column(sa.DateTime(timezone=True), default=sa.func.now())
	updated_at = sa.Column(sa.DateTime(timezone=True), onupdate=sa.func.now())
