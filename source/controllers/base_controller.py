from abc import ABC, abstractmethod
from telebot.types import InlineKeyboardButton


class BaseController(ABC):

    @abstractmethod
    def callback_name(self) -> str:
        pass

    def get_menu_btn(self) -> InlineKeyboardButton:
        pass
