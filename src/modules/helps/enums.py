from enum import Enum


class Command(str, Enum):
    """Виды команд"""

    OPERATIONS = 'operations'
    START = 'start'
    HELP = 'help'
    BUDGET = 'budget'
    TODAY = 'today'
    MONTH = 'month'
    WALLETS = 'wallets'
    WALLET = 'wallet'
