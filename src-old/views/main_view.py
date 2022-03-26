from views.base_view import BaseView
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


class MainView(BaseView):

    def __init__(self, menu: list):
        self._menu = menu

    def get_menu_markup(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        [markup.add(item) for item in self._menu]
        return markup
