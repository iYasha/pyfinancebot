from config import dp, bot, settings
from aiogram import types

from modules.helps.enums import Command
from sdk.exceptions.handler import error_handler_decorator


@dp.message_handler(commands=[Command.HELP])
@error_handler_decorator
async def get_help(message: types.Message):
    text = '<b>Доступные команды:</b>\n\n' \
           f'• /{Command.START} - Начать использовать бота\n' \
           f'• /{Command.BUDGET} - Получить информацию о бюджете\n' \
           f'• /{Command.TODAY} - Получить информацию о бюджете сегодня\n' \
           f'• /{Command.WALLETS} - Просмотреть мои кошельки\n' \
           f'• /{Command.HELP} - Показать все доступные команды\n'
    await bot.send_message(message.chat.id, text=text, parse_mode=settings.PARSE_MODE)
