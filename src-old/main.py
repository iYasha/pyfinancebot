import sqlite3
import telebot

import logging

from controllers.none_controller import NoneController
from controllers.main_controller import MainController
from controllers.receipt_controller import ReceiptController


def init_db(cursor: sqlite3.Cursor):
    cursor.execute(' \
        CREATE TABLE IF NOT EXISTS `users` \
        ( `chat_id` INT NOT NULL , `username` VARCHAR(255) NOT NULL , \
         `company_id` INT NULL , `message_id` INT NOT NULL , `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP , \
          PRIMARY KEY (`chat_id`)) \
        '
                   )
    cursor.execute('CREATE TABLE IF NOT EXISTS `receipts`('
                   'id INTEGER not null PRIMARY KEY autoincrement,'
                   'chat_id INT not null,'
                   'created_at TIMESTAMP not null,'
                   'shop_name VARCHAR(255) null,'
                   'amount INT null,'
                   'address VARCHAR(255) null,'
                   'lat DOUBLE null,'
                   'lng INT null,'
                   'buy_time VARCHAR(255) null,'
                   'image_path VARCHAR(255) null);')


# def set_logger():
#     # Логи
#     telebot.logger.setLevel(logging.INFO)
#     fileh = logging.FileHandler(env.get('LOG_PATH'), 'a')
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     fileh.setFormatter(formatter)
#     telebot.logger.addHandler(fileh)


def main():
    bot = telebot.TeleBot('1209681927:AAFcSOzHDwLs5j0hKER3wldSuZSPZdTaelE')

    conn = sqlite3.connect('./', check_same_thread=False, isolation_level=None)
    cursor: sqlite3.Cursor = conn.cursor()
    init_db(cursor)

    none_controller = NoneController(bot)
    receipt_controller = ReceiptController(bot, cursor)
    menu = [
        receipt_controller.get_menu_btn()
    ]
    main_controller = MainController(bot, menu, cursor)

    bot.skip_pending = True
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()
