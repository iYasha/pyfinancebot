from datetime import datetime
from typing import List, Optional, Union

from crud.base import BaseCRUD
from crud.base import BasePaginator

import sqlalchemy as sa
from core.database import database
import schemas
import models
import enums


class WalletCRUD(BaseCRUD):
    _model = models.Wallet
    _model_schema = schemas.WalletInDBSchema
    _model_create_schema = schemas.WalletCreateSchema
