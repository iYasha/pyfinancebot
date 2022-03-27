from typing import List, Optional

from crud.base import BaseCRUD
from crud.base import BasePaginator

import sqlalchemy as sa
from core.database import database
import schemas
import models
import enums


class OperationCRUD(BaseCRUD):
    _model = models.Operation
    _model_schema = schemas.OperationInDBSchema
    _model_create_schema = schemas.OperationCreateSchema
    _paginator = BasePaginator

    @classmethod
    async def get_regular_operation(
            cls,
            is_approved: bool = True,
            is_regular_operation: bool = True,
            has_full_amount: Optional[bool] = None,
    ) -> List[schemas.OperationInDBSchema]:
        query = cls.get_base_query()
        where = [
            cls._model.repeat_type != enums.RepeatType.NO_REPEAT,
            cls._model.is_approved == is_approved,
            cls._model.is_regular_operation == is_regular_operation
        ]
        if has_full_amount is not None:
            if has_full_amount:
                where.append(cls._model.amount == cls._model.received_amount)
            else:
                where.append(sa.or_(cls._model.amount != cls._model.received_amount, cls._model.received_amount == None))
        query = query.where(*where)
        results = await database.fetch_all(query)
        return [cls._get_parsed_object(obj) for obj in results]
