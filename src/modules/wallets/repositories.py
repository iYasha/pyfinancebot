from sdk.base import BaseCRUD

import schemas
import models


class WalletCRUD(BaseCRUD):
    _model = models.Wallet
    _model_schema = schemas.WalletInDBSchema
    _model_create_schema = schemas.WalletCreateSchema
