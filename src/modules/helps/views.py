from aiogram import types

from config import bot, dp, settings
from modules.helps.enums import Command
from sdk.decorators import error_handler_decorator


@dp.message_handler(commands=[Command.HELP])
@error_handler_decorator
async def get_help(message: types.Message) -> None:
    text = (
        '<b>Добро пожаловать в бота для учета финансов!</b>\n'
        'Данный бот поможет вам вести учет финансов и планировать бюджет.\n'
        'Для начала работы вам необходимо вступить или создать компанию - /companies\n'
        'После этого вы сможете добавлять операции и планировать бюджет.\n\n'
        '<b>Базовые операции</b>\n'
        'Примеры базовых операций:\n'
        '<code>-1300 грн за продукты</code>\n'
        '<code>+500 usd зарплата</code>\n'
        '<code>-8000 грн за аренду квартиру</code>\n'
        '<code>+1000 грн подарок</code>\n\n'
        '<b>Регулярные операции</b> - тип операции, которые повторяются раз в определенное время.\n'
        'Примеры регулярных операций:\n'
        '<code>-8000 грн за аренду квартиры каждое 10 число</code>\n'
        '<code>-7 usd за подписку YouTube Family каждое 4 число</code>\n'
        '<code>+1000 usd аванс на работе каждое 25 число</code>\n'
        '<code>-360 грн каждое последнее число месяца за интернет</code>\n'
        '<code>-310 грн за теннис каждый понедельник, вторник, четверг и субботу</code>\n\n'
        '<b>Доступные команды:</b>\n'
        f'• /{Command.START} - Начать использовать бота\n'
        f'• /{Command.TODAY} - Получить информацию о бюджете сегодня\n'
        f'• /{Command.MONTH} - Получить информацию о бюджете за месяц\n'
        f'• /{Command.OPERATIONS} - Просмотреть все операции\n'
        f'• /{Command.REGULAR} - Просмотреть все регулярные операции\n'
        f'• /{Command.FUTURE} - Просмотреть все будущие операции\n'
        f'• /{Command.COMPANIES} - Просмотреть все компании\n'
        f'• /{Command.CHOOSE_COMPANY} - Выбрать компанию\n'
        f'• /{Command.HELP} - Показать все доступные команды\n'
    )
    await bot.send_message(message.chat.id, text=text, parse_mode=settings.PARSE_MODE)
