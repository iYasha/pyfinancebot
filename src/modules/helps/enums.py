from enum import Enum


class Command(str, Enum):
    """Виды команд"""

    START = 'start'
    HELP = 'help'
    BUDGET = 'budget'
    TODAY = 'today'
    WALLETS = 'wallets'
    WALLET = 'wallet'
