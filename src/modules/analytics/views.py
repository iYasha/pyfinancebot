import datetime
from typing import Union

from aiogram import types
from config import bot
from config import dp
from config import settings
from modules.helps.enums import Command
from modules.operations.enums import BackScreenType
from modules.operations.enums import OperationType
from modules.operations.services import OperationService

from sdk import utils
from sdk.decorators import error_handler_decorator
from sdk.decorators import select_company_required
from sdk.utils import round_amount


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(Command.TODAY),
)
@dp.message_handler(commands=[Command.TODAY])
@select_company_required
@error_handler_decorator
async def get_today_analytics(data: Union[types.Message, types.CallbackQuery]) -> None:
    if isinstance(data, types.CallbackQuery):
        chat_id = data.message.chat.id
    else:
        chat_id = data.chat.id
    month_date_from, month_date_to = await utils.get_current_month_period()
    date_from, date_to = await utils.get_current_day_period()
    company_id = settings.SELECTED_COMPANIES.get(chat_id)
    today_stats = await OperationService.get_stats(
        date_from=date_from,
        date_to=date_to,
        company_id=company_id,
    )
    month_stats = await OperationService.get_stats(
        date_from=month_date_from,
        date_to=month_date_to,
        company_id=company_id,
    )
    future_operations = await OperationService.get_future_operations(company_id)
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
    saldo = month_stats['income'] + future_income - month_stats['expense'] - future_expense
    days_left = (month_date_to - date_from).days
    if days_left == 0:
        days_left = 1
    day_budget = round(saldo / days_left, 2)
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
            chat_id=chat_id,
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
@select_company_required
@error_handler_decorator
async def get_month_analytics(message: types.Message) -> None:
    date_from, date_to = await utils.get_current_month_period()
    now_day = datetime.datetime.now().day
    company_id = settings.SELECTED_COMPANIES.get(message.chat.id)
    stats = await OperationService.get_stats(
        date_from=date_from,
        date_to=date_to,
        company_id=company_id,
    )
    income, expense = stats['income'], stats['expense']
    future_operations = await OperationService.get_future_operations(company_id)
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
    saldo = income + future_income - expense - future_expense
    days_left = date_to.day - now_day
    if days_left == 0:
        days_left = 1
    day_budget = round(saldo / days_left, 2)
    await message.answer(
        f'🟢 Доход: {round_amount(income, 2)}₴\n🔴 Расход: {round_amount(expense, 2)}₴\n'
        f'💸 Баланс: {round_amount(saldo, 2)}₴\n'
        f'💰 Дневной бюджет: {round_amount(day_budget, 2)}₴\n\n'
        f'🟢 Future income {round_amount(future_income, 2)}₴\n🔴 Future expense {round_amount(future_expense, 2)}₴',
    )
