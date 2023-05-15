import datetime
from typing import Union

from aiogram import types
from config import bot
from config import dp
from modules.helps.enums import Command
from modules.operations.enums import BackScreenType
from modules.operations.enums import OperationType
from modules.operations.services import OperationService

from sdk import utils
from sdk.exceptions.handler import error_handler_decorator
from sdk.utils import round_amount


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(Command.TODAY),
)
@dp.message_handler(commands=[Command.TODAY])
@error_handler_decorator
async def get_today_analytics(data: Union[types.Message, types.CallbackQuery]) -> None:
    month_date_from, month_date_to = await utils.get_current_month_period()
    date_from, date_to = await utils.get_current_day_period()
    today_stats = await OperationService.get_stats(date_from=date_from, date_to=date_to)
    month_stats = await OperationService.get_stats(date_from=month_date_from, date_to=month_date_to)
    future_operations = await OperationService.get_future_operations()
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    future_expense = sum(
        [
            operation.amount
            for operation in future_operations
            if operation.operation_type == OperationType.EXPENSE
        ],
    )
    future_income = sum(
        [
            operation.amount
            for operation in future_operations
            if operation.operation_type == OperationType.INCOME
        ],
    )
    tomorrow_operations = tuple(
        filter(lambda x: x.created_at.date() == tomorrow.date(), future_operations),
    )
    saldo = month_stats['income'] + future_income - month_stats['expense'] + future_expense
    day_budget = round(saldo / (month_date_to.day - date_from.day), 2)
    message_text = (
        f'🟢 Доход: {round_amount(today_stats["income"], 2)}₴\n🔴 Расход: {round_amount(today_stats["expense"], 2)}₴\n'
        f'💸 Баланс: {round_amount(saldo, 2)}₴\n'
        f'💰 Дневной бюджет: {round_amount(day_budget, 2)}₴\n\n'
        f'🟢 Future income {round_amount(future_income, 2)}₴\n🔴 Future expense {round_amount(future_expense, 2)}₴\n\n'
        f'Операции на завтра:\n'
    )
    markup = utils.get_future_operation_markup(tomorrow_operations, BackScreenType.TODAY)
    if isinstance(data, types.CallbackQuery):
        await bot.edit_message_text(
            chat_id=data.message.chat.id,
            message_id=data.message.message_id,
            text=message_text,
            reply_markup=markup,
        )
    else:
        await data.answer(
            text=message_text,
            reply_markup=markup,
        )


@dp.message_handler(commands=[Command.MONTH])
@error_handler_decorator
async def get_month_analytics(message: types.Message) -> None:
    date_from, date_to = await utils.get_current_month_period()
    now_day = datetime.datetime.now().day
    stats = await OperationService.get_stats(date_from=date_from, date_to=date_to)
    income, expense = stats['income'], stats['expense']
    future_operations = await OperationService.get_future_operations()
    future_expense = sum(
        [
            operation.amount
            for operation in future_operations
            if operation.operation_type == OperationType.EXPENSE
        ],
    )
    future_income = sum(
        [
            operation.amount
            for operation in future_operations
            if operation.operation_type == OperationType.INCOME
        ],
    )
    saldo = income + future_income - expense + future_expense
    day_budget = round(saldo / (date_to.day - now_day), 2)
    await message.answer(
        f'🟢 Доход: {round_amount(income, 2)}₴\n🔴 Расход: {round_amount(expense, 2)}₴\n'
        f'💸 Баланс: {round_amount(saldo, 2)}₴\n'
        f'💰 Дневной бюджет: {round_amount(day_budget, 2)}₴\n\n'
        f'🟢 Future income {round_amount(future_income, 2)}₴\n🔴 Future expense {round_amount(future_expense, 2)}₴',
    )
