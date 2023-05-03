import datetime

from aiogram import types
from config import dp
from modules.helps.enums import Command
from modules.operations.services import OperationService

from sdk import utils
from sdk.exceptions.handler import error_handler_decorator
from sdk.utils import round_amount


@dp.message_handler(commands=[Command.TODAY])
@error_handler_decorator
async def get_today_analytics(message: types.Message) -> None:
    date_from, date_to = await utils.get_current_month_period()
    now_day = datetime.datetime.now().day
    stats = await OperationService.get_stats(date_from=date_from, date_to=date_to)
    income, expense = stats['income'], stats['expense']
    saldo = income - expense
    day_budget = round(saldo / (date_to.day - now_day), 2)
    await message.answer(
        f'🟢 Доход: {round_amount(income, 2)}₴\n🔴 Расход: {round_amount(expense, 2)}₴\n'
        f'💸 Баланс: {round_amount(saldo, 2)}₴\n'
        f'💰 Дневной бюджет: {round_amount(day_budget, 2)}₴',
    )
