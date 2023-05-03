import models
import schemas
from sdk.base import BaseCRUD


class WalletCRUD(BaseCRUD):
    _model = models.Wallet
    _model_schema = schemas.WalletInDBSchema
    _model_create_schema = schemas.WalletCreateSchema
