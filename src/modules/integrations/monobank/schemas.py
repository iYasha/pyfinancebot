from enum import Enum
from typing import List, Optional

from pydantic import Field

from sdk.schemas import BaseSchema


# Enum for Account Types
class AccountType(str, Enum):
    BLACK = 'black'
    WHITE = 'white'
    PLATINUM = 'platinum'
    IRON = 'iron'
    FOP = 'fop'
    eAID = 'eAid'
    YELLOW = 'yellow'


# Enum for Cashback Types
class CashbackType(str, Enum):
    NONE = 'None'
    UAH = 'UAH'
    MILES = 'Miles'
    # Add more cashback types if needed


# Enum for Client Permissions
class ClientPermissions(str, Enum):
    READ = 'read'
    WRITE = 'write'
    FULL_ACCESS = 'full_access'
    # Add more permissions if needed


# Schema for Currency Info
class CurrencyInfo(BaseSchema):
    currencyCodeA: int
    currencyCodeB: int
    date: int
    rateSell: Optional[float] = None
    rateBuy: Optional[float] = None
    rateCross: Optional[float] = None


# Schema for WebHook URL setup
class SetWebHookRequest(BaseSchema):
    webHookUrl: str


# Schema for Account Details
class AccountInfo(BaseSchema):
    id: str
    sendId: str
    balance: int
    creditLimit: int
    type: AccountType  # Use Enum for account type
    currencyCode: int
    cashbackType: Optional[CashbackType] = None  # Use Enum for cashback type
    maskedPan: List[str]
    iban: Optional[str] = None  # Make IBAN optional


# Schema for Bank Jar details
class BankJar(BaseSchema):
    id: str
    sendId: str
    title: str
    description: Optional[str] = None  # Make description optional
    currencyCode: int
    balance: int
    goal: int


# Schema for Client Information
class ClientInfo(BaseSchema):
    clientId: str
    name: str
    webHookUrl: Optional[str] = None  # Make webhook URL optional
    permissions: str
    accounts: List[AccountInfo]
    jars: List[BankJar] = Field(default_factory=list)


# Schema for Statement Item
class StatementItem(BaseSchema):
    id: str
    time: int
    description: str
    mcc: int
    originalMcc: Optional[int] = None  # Make originalMCC optional
    hold: bool
    amount: int
    operationAmount: int
    currencyCode: int
    commissionRate: int
    cashbackAmount: int
    balance: int


# Schema for List of Statement Items (Transactions)
class StatementItems(BaseSchema):
    items: List[StatementItem]
