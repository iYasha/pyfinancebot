from core.config import settings
from aiogram import types

import enums


@settings.dp.message_handler(commands=[enums.Command.HELP])
async def get_help(message: types.Message):
    text = '<b>Доступные команды:</b>\n\n' \
           f'• /{enums.Command.START} - Начать использовать бота\n' \
           f'• /{enums.Command.BUDGET} - Получить информацию о бюджете\n' \
           f'• /{enums.Command.TODAY} - Получить информацию о бюджете сегодня\n' \
           f'• /{enums.Command.HELP} - Показать все доступные команды\n'
    await settings.bot.send_message(message.chat.id, text=text, parse_mode=settings.PARSE_MODE)
