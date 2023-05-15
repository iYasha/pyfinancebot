from enum import Enum


class Command(str, Enum):
    """Виды команд"""

    OPERATIONS = 'operations'
    FUTURE = 'future'
    REGULAR = 'regular'
    START = 'start'
    HELP = 'help'
    TODAY = 'today'
    MONTH = 'month'
