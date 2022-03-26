from crud.base import BaseCRUD
from crud.base import BasePaginator

import schemas
import models


class OperationCRUD(BaseCRUD):
    _model = models.Operation
    _model_schema = schemas.OperationInDBSchema
    _model_create_schema = schemas.OperationCreateSchema
    _paginator = BasePaginator

    pass
