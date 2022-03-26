from models.base_model import BaseModel
from models.main_model import User
import telebot

import sqlite3


class MsgModel(BaseModel):

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    def get_last_msg(self, chat_id: int) -> int:
        try:
            request = f'SELECT {", ".join([x for x in User.__annotations__])} ' \
                      f'FROM `users` WHERE `chat_id` = {chat_id}'
            self._cursor.execute(request)
            user: User = User(*self._cursor.fetchone())
            return user.message_id
        except Exception as e:
            telebot.logger.error(e)
            return False

    def update_last_msg(self, chat_id: int, msg_id: int) -> bool:
        try:
            request = 'UPDATE `users`' \
                     f' SET `message_id` = {msg_id}' \
                     f' WHERE `chat_id` = {chat_id}'
            self._cursor.execute(request)
            return True
        except Exception as e:
            telebot.logger.error(e)
            return False
