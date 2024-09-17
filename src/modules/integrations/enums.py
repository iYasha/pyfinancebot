from enum import Enum


class AvailableIntegration(str, Enum):
    UNIQUE_PREFIX = 'int_'

    MONOBANK = UNIQUE_PREFIX + 'monobank'
