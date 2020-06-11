from .base_controller import BaseController
from telebot import TeleBot
import telebot
from telebot.types import InlineKeyboardButton
import os
import sqlite3

from views.main_view import MainView as View
from models.main_model import MainModel as Model
from models.main_model import User

from controllers.message_controller import MsgController as Msg


class MainController(BaseController):

    def callback_name(self) -> str:
        return 'mn_'

    def get_menu_btn(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(text="Главная", callback_data=self.callback_name())

    def __init__(self, bot: TeleBot, menu: list, db: sqlite3.Cursor):
        self._bot = bot
        self._view = View(menu)
        self._model = Model(db)
        self._msg = Msg(db, bot)

        @self._bot.message_handler(commands=['start'])
        def send_welcome(msg, is_callback: bool = False) -> None:
            if not is_callback:
                try:  # если пользователь долго не заходил в чат, то мы не сможем удалить его сообщение
                    self._bot.delete_message(msg.chat.id, msg.message_id)
                except Exception as e:
                    telebot.logger.error(e)
            if msg.chat.first_name is not None and msg.chat.last_name is not None:
                username = msg.chat.first_name + ' ' + msg.chat.last_name
            else:
                username = msg.chat.username
            user = User(chat_id=msg.chat.id, username=msg.chat.username, message_id=msg.message_id)
            self._model.create_or_not_user(user)
            text = self._model.get_welcome_text()
            markup = self._view.get_menu_markup()

            self._msg.send_message(
                chat_id=msg.chat.id,
                text=text % username,
                reply_markup=markup,
                parse_mode=None,
                reply_main_markup=False,
                status='new'
            )

        @bot.callback_query_handler(func=lambda call: call.data.find(self.callback_name()) != -1)
        def _send_welcome_callback(call) -> None:
            send_welcome(call.message, True)
