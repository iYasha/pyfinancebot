from .base_controller import BaseController
from telebot import TeleBot
from telebot.types import InlineKeyboardButton
from repositories.callback_types import NoneCallback


class NoneController(BaseController):

    def callback_name(self) -> str:
        return self.callback_name

    def get_menu_btn(self) -> InlineKeyboardButton:
        pass

    def __init__(self, bot: TeleBot):
        self._bot = bot
        self.none_callback = NoneCallback()
        self.callback_name = self.none_callback.text

        @bot.callback_query_handler(func=lambda call: call.data.find(self.callback_name) != -1)
        def _none_callback(call) -> None:
            self.none_callback.func()
