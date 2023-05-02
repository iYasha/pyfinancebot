from config import settings
from aiogram import types

import enums


@settings.dp.message_handler(commands=[enums.Command.WALLETS])
async def get_wallets(message: types.Message):
    text = '<b>Доступные команды:</b>\n\n' \
           f'• /{enums.Command.START} - Начать использовать бота\n' \
           f'• /{enums.Command.BUDGET} - Получить информацию о бюджете\n' \
           f'• /{enums.Command.TODAY} - Получить информацию о бюджете сегодня\n' \
           f'• /{enums.Command.HELP} - Показать все доступные команды\n'
    await settings.bot.send_message(message.chat.id, text=text, parse_mode=settings.PARSE_MODE)


@settings.dp.message_handler(commands=[enums.Command.WALLET])
async def create_wallet(message: types.Message):
    wallet_name = message.get_args()
    if not wallet_name:
        await settings.bot.send_message(message.chat.id, text='❌ Введите название кошелька: <b>/wallet название</b>', parse_mode=settings.PARSE_MODE)
        return
    await settings.bot.send_message(message.chat.id, text=f'Wallet name: {wallet_name}', parse_mode=settings.PARSE_MODE)
