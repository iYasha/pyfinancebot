from typing import Type

from modules.integrations.monobank.models import MonobankIntegration
from sdk.repositories import BaseRepository


class MonobankIntegrationRepository(BaseRepository):
    model: Type[MonobankIntegration] = MonobankIntegration
