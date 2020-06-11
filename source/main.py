import sqlite3
import telebot

import logging

from config.enviroment import env
from controllers.none_controller import NoneController
from controllers.main_controller import MainController


def init_db(cursor: sqlite3.Cursor):
    cursor.execute(' \
        CREATE TABLE IF NOT EXISTS `users` \
        ( `chat_id` INT NOT NULL , `username` VARCHAR(255) NOT NULL , \
         `company_id` INT NULL , `message_id` INT NOT NULL , `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP , \
          PRIMARY KEY (`chat_id`)) \
        '
    )


def set_logger():
    # Логи
    telebot.logger.setLevel(logging.INFO)
    fileh = logging.FileHandler(env.get('LOG_PATH'), 'a')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileh.setFormatter(formatter)
    telebot.logger.addHandler(fileh)


def main():
    bot = telebot.TeleBot(env.get('TELEGRAM_API_TOKEN'))

    set_logger()

    conn = sqlite3.connect(env.get('DATABASE_PATH'), check_same_thread=False, isolation_level=None)
    cursor: sqlite3.Cursor = conn.cursor()
    init_db(cursor)

    none_controller = NoneController(bot)
    menu = [

    ]
    main_controller = MainController(bot, menu, cursor)

    bot.skip_pending = True
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()
