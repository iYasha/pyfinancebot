import sqlite3
from telebot import TeleBot
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice

from models.message_model import MsgModel as Model


class MsgController:

    def __init__(self, cursor: sqlite3.Cursor, bot: TeleBot):
        self._bot = bot
        self._model = Model(cursor)

    def send_message(self, chat_id: int, text: str, reply_markup=None, parse_mode: str or None = "Markdown",
                     status: str = "old", reply_main_markup: bool = True):
        if reply_main_markup:
            if reply_markup is not None:
                reply_markup.add(InlineKeyboardButton(text='◀️ На главную', callback_data='mn_'))
            else:
                reply_markup = InlineKeyboardMarkup()
                reply_markup.add(InlineKeyboardButton(text='◀️ На главную', callback_data='mn_'))
        if status == "old":
            last_msg: int or bool = self._model.get_last_msg(chat_id)
        else:
            last_msg = 0
        if not last_msg:
            last_msg = 0
        else:
            last_msg = last_msg
        if last_msg == 0:
            if reply_markup is not None:
                msg = self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode,
                                             reply_markup=reply_markup)
            else:
                msg = self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        else:
            try:
                if reply_markup is not None:
                    msg = self._bot.edit_message_text(chat_id=chat_id, message_id=last_msg, text=text,
                                                      parse_mode=parse_mode, reply_markup=reply_markup)
                else:
                    msg = self._bot.edit_message_text(chat_id=chat_id, message_id=last_msg, text=text,
                                                      parse_mode=parse_mode)
            except Exception as e:
                telebot.logger.error(e)
                if reply_markup is not None:
                    msg = self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode,
                                                 reply_markup=reply_markup)
                else:
                    msg = self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        self._model.update_last_msg(chat_id, msg.message_id)
        self._bot.clear_step_handler_by_chat_id(chat_id)
        return msg
