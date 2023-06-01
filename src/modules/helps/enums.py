from enum import Enum


class Command(str, Enum):
    """Виды команд"""

    CHOOSE_COMPANY = 'choose_company'
    OPERATIONS = 'operations'
    FUTURE = 'future'
    REGULAR = 'regular'
    START = 'start'
    HELP = 'help'
    TODAY = 'today'
    MONTH = 'month'
    COMPANIES = 'companies'
