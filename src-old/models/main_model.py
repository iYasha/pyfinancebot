from models.base_model import BaseModel
import sqlite3
from dataclasses import dataclass


@dataclass
class User:
    chat_id: int
    username: str
    message_id: int
    company_id: int or None = None


class MainModel(BaseModel):

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    @staticmethod
    def get_welcome_text() -> str:
        return 'Привет %s. С чего начнем ?'

    def create_or_not_user(self, user: User):
        request = 'INSERT OR REPLACE INTO `users`' \
                  '(`chat_id`, `username`, `company_id`, `message_id`, `created_at`) ' \
                  f'VALUES({user.chat_id}, "{user.username}", {user.company_id if user.company_id is not None else "NULL" }, {user.message_id}, CURRENT_TIMESTAMP);'
        self._cursor.execute(request)
