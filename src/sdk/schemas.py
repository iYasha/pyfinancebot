from datetime import datetime, timezone
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

from config import settings


class BaseSchema(BaseModel):
    class Config:
        json_encoders = {datetime: lambda dt: dt.strftime(settings.DEFAULT_DATETIME_FORMAT)}


BaseSchemaType = TypeVar('BaseSchemaType', bound=BaseSchema)


class IDSchemaMixin(BaseSchema):
    id: int


class PaginatedSchema(BaseModel, Generic[BaseSchemaType]):
    total_count: int = 0
    page_count: int
    next: Optional[int]  # noqa: VNE003
    previous: Optional[int]
    results: List[BaseSchemaType]


class ExpireSchemaMixin(BaseSchema):
    start_at: datetime
    end_at: datetime

    @property
    def block_pass_time(self) -> int:
        utc_now = datetime.now(timezone.utc)
        return (self.end_at - utc_now).seconds


class SoftDeleteSchemaMixin(BaseSchema):
    deleted_at: Optional[datetime] = None


class TrackingSchemaMixin(BaseSchema):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditSchemaMixin(BaseSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
