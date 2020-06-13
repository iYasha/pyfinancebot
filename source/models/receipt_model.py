from models.base_model import BaseModel
import sqlite3
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional


@dataclass
class Point:
    lat: float = 0.0
    lng: float = 0.0


@dataclass
class City:
    address: str = ''
    location: Point = Point()


@dataclass_json
@dataclass
class Receipt:
    chat_id: int
    created_at: int
    shop_name: Optional[str] = None
    amount: Optional[float] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    buy_time: Optional[str] = None
    image_path: Optional[str] = None


class ReceiptModel(BaseModel):
    # Text markup
    exception_receipt_text: str = '⚠️ <b>Произошла ошибка: </b> ⚠️\n' \
                                  '<code>%s</code>\n\n' \
                                  'Попробуйте повторить действие позже, или сообщите в тех поддержку ' \
                                  '<b>@iYashaDesign</b> '
    success_parse_receipt: str = '🎰 <b>Информация получена</b> 🎰\n\n' \
                                 '<i>Название магазина:</i> <code>%s</code>\n' \
                                 '<i>Сумма чека:</i> <code>%.2f грн</code>\n' \
                                 '<i>Адрес магазина:</i> <code>%s</code>\n' \
                                 '<i>Дата и время:</i> <code>%s</code>\n'

    # Text
    receipt_main_text: str = 'Ваши чеки: '
    scan_text: str = 'Пришлите фото чека следующим сообщением'

    # Exceptions
    photo_not_found = 'Фотография не найдена'
    cant_save_receipt = 'Не удалось сохранить файл'
    cant_get_receipt_info = 'Не удалось получить информацию из чека'

    def __init__(self, db: sqlite3.Cursor):
        self._db = db

    def get_receipts(self, chat_id: int, limit=5):
        return []

    def create_receipt(self, receipt: Receipt) -> int:
        values = ", ".join(["'" + str(x).replace('"', '').replace("'", '') + "'" for x in receipt.to_dict().values()])
        request = 'INSERT OR REPLACE INTO `receipts`' \
                  f'({", ".join([x for x in Receipt.__annotations__])}) ' \
                  f'VALUES({values});'
        return self._db.execute(request).lastrowid
