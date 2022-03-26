from .base_controller import BaseController
from telebot import TeleBot
import telebot
from telebot.types import InlineKeyboardButton, Message
import sqlite3
from core.config import env
from typing import Optional, Tuple, Union
from google.cloud import vision
import io
import os
import difflib
import requests
import math
from datetime import datetime

from models.receipt_model import City, Point, Receipt

from views.receipt_view import ReceiptView as View
from models.receipt_model import ReceiptModel as Model
from repositories.exceptions import CantDetectReceipt

from controllers.message_controller import MsgController as Msg

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = env.get('GOOGLE_APPLICATION_CREDENTIALS')


class ReceiptController(BaseController):

    def callback_name(self, additive: str = '') -> str:
        return f'rc_{additive}'

    def get_menu_btn(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(text="История заказов", callback_data=self.callback_name())

    def _save_receipt(self, mime_type: str, file_id: str) -> Optional[str]:
        if str(mime_type).index("image") != -1:
            file_id = file_id
            file_info = self._bot.get_file(file_id)
            download_path = env.get('STORAGE_PATH') + '/receipts'
            downloaded_file = self._bot.download_file(file_info.file_path)
            download_path = f'{download_path}/{file_id}.jpg'
            with open(download_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                return download_path
        return None

    def _get_data_from_receipt(self, msg: Message, is_callback: bool = False):

        def is_shop_name(name: str):
            shop_names = ['АТБ', 'Копійка', 'Сільпо']
            layout = dict(zip(map(ord, 'TOBATMPKI'), 'ТОВАТМРКІ'))
            name = name.upper().translate(layout)
            shop_weight = {}
            for i in shop_names:
                shop_weight[i] = difflib.SequenceMatcher(None, name, i.upper()).ratio()
            return shop_weight

        def parse_data(path: str) -> Tuple[Optional[float], Optional[str], City, Union[datetime, str]]:
            client = vision.ImageAnnotatorClient()

            with io.open(path, 'rb') as image_file:
                content = image_file.read()

            image = vision.types.Image(content=content)

            response = client.text_detection(image=image)
            texts = response.text_annotations

            amount = None
            weights = []

            city_address = ''
            start_write_address = False
            count_addresses = 0
            receipt_datetime: Optional[datetime] = None

            for idx, text in enumerate(texts):
                if text.description.find('-') != -1 and idx != 0:
                    try:
                        date = text.description
                        date = str(date).replace('28', '20')
                        receipt_datetime = datetime.strptime(
                            f'{date} {texts[idx + 1].description}', '%d-%m-%Y %H:%M:%S'
                        )
                    except ValueError:
                        pass
                if text.description.upper() == 'CYMA' \
                        or text.description.upper() == 'СУМА' \
                        or text.description.upper() == 'СУНА' \
                        or text.description.upper() == 'КАРТКА':
                    try:
                        amount = float(texts[idx + 1].description.replace(',', '.'))
                    except ValueError:
                        pass
                elif idx < 10:
                    weights.append(is_shop_name(text.description))
                if text.description.upper() == 'M.' or text.description.upper() == 'Н.':
                    start_write_address = True
                elif count_addresses == 4:
                    start_write_address = False
                if start_write_address:
                    count_addresses += 1
                    city_address += text.description + ' '
            max_weight = 0.0
            shop_name = None
            for weight in weights:
                for name in weight:
                    if weight[name] > max_weight:
                        max_weight = weight[name]
                        shop_name = name
            api_key = env.get('GOOGLE_MAPS_API_KEY')
            city = City()
            if len(city_address) > 0:
                response = requests.get(
                    url=f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={city_address}&inputtype=textquery&fields=photos,formatted_address,name,rating,opening_hours,geometry&key={api_key}')
                if 200 <= response.status_code <= 299:
                    resp_dict = response.json()
                    if resp_dict['status'] == 'OK' and len(resp_dict['candidates']) > 0:
                        city.address = resp_dict['candidates'][0]['formatted_address']
                        city.location.lat = resp_dict['candidates'][0]['geometry']['location']['lat']
                        city.location.lng = resp_dict['candidates'][0]['geometry']['location']['lng']

            return amount, shop_name, city, receipt_datetime

        try:
            if msg.photo is not None:
                file_id = msg.photo[-1].file_id
                mime_type = 'image'
            elif msg.document is not None:
                file_id = msg.document.file_id
                mime_type = msg.document.mime_type
            else:
                raise CantDetectReceipt(self._model.photo_not_found)
            file_path = self._save_receipt(mime_type, file_id)
            self._bot.delete_message(message_id=msg.message_id, chat_id=msg.chat.id)

            if file_path is None:
                raise CantDetectReceipt(self._model.cant_save_receipt)

            amount, shop_name, city, receipt_datetime = parse_data(file_path)

            if amount is None or shop_name is None:
                os.remove(file_path)
                raise CantDetectReceipt(self._model.cant_get_receipt_info)

            if receipt_datetime is None:
                receipt_datetime = 'Не удалось определить дату и время'
            else:
                receipt_datetime = receipt_datetime.strftime('%d.%m.%Y %H:%M:%S')

            text = self._model.success_parse_receipt % (
                shop_name,
                amount,
                (city.address if len(city.address) > 0 else 'Не удалось получить адрес'),
                receipt_datetime
            )
            markup = self._view.get_receipt_shop_address_markup(
                cb=self.callback_name(f'l_{city.location.lat}_{city.location.lng}'))
            self._msg.send_message(
                chat_id=msg.chat.id,
                text=text,
                reply_markup=markup if len(city.address) > 0 else None,
                parse_mode="HTML"
            )
            receipt = Receipt(
                shop_name=shop_name,
                amount=amount,
                address=city.address,
                lat=city.location.lat,
                lng=city.location.lng,
                buy_time=receipt_datetime,
                chat_id=msg.chat.id,
                created_at=math.ceil(datetime.now().timestamp()),
                image_path=file_path
            )
            receipt_id = self._model.create_receipt(receipt)
        except CantDetectReceipt as e:
            error_text = self._model.exception_receipt_text
            self._msg.send_message(
                chat_id=msg.chat.id,
                text=error_text % str(e),
                parse_mode="HTML",
            )

    def __init__(self, bot: TeleBot, db: sqlite3.Cursor):
        self._bot = bot
        self._view = View()
        self._model = Model(db)
        self._msg = Msg(db, bot)

        @self._bot.message_handler(commands=['receipt'])
        def send_receipt(msg: Message, is_callback: bool = False) -> None:
            if not is_callback:
                try:  # если пользователь долго не заходил в чат, то мы не сможем удалить его сообщение
                    self._bot.delete_message(msg.chat.id, msg.message_id)
                except Exception as e:
                    telebot.logger.error(e)
            text = self._model.receipt_main_text
            receipts = self._model.get_receipts(chat_id=msg.chat.id, limit=5)
            markup = self._view.get_receipts_markup(self.callback_name('show'), self.callback_name('scan'), receipts)
            self._msg.send_message(
                chat_id=msg.chat.id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown",
            )

        @bot.callback_query_handler(func=lambda call: call.data.find(self.callback_name('l_')) != -1)
        def _order_status(call) -> None:
            self._bot.answer_callback_query(call.id, text='Загрузка')
            points = Point(*call.data.replace(self.callback_name('l_'), '').split('_'))
            self._bot.send_location(call.message.chat.id, points.lat, points.lng)

        @bot.callback_query_handler(func=lambda call: call.data.find(self.callback_name('scan')) != -1)
        def _order_status(call) -> None:
            msg = self._msg.send_message(
                chat_id=call.message.chat.id,
                text=self._model.scan_text,
            )
            self._bot.answer_callback_query(call.id, text='Загрузка')
            self._bot.register_next_step_handler_by_chat_id(call.message.chat.id, self._get_data_from_receipt)

        @bot.callback_query_handler(func=lambda call: call.data.find(self.callback_name()) != -1)
        def _send_receipt_callback(call) -> None:
            send_receipt(call.message, True)
