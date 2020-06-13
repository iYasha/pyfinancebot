from views.base_view import BaseView
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from repositories.callback_types import NoneCallback


class ReceiptView(BaseView):


    def get_receipts_markup(self, cb: str, sc_cb: str, receipts: list) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Отсканировать чек', callback_data=sc_cb))
        return markup


    def get_receipt_shop_address_markup(self, cb: str) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text='Получить карту', callback_data=cb))
        return markup