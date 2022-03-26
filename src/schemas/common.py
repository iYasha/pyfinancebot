from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class PaginatedSchema(GenericModel, Generic[BaseModelType]):
    count: int
    next: Optional[int]  # noqa: A003
    previous: Optional[int]
    results: List[BaseModelType]


class Pagination(BaseModel):
    page: int = 0
    page_size: int = 10
