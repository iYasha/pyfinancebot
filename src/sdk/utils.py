import calendar
import datetime
import re
from typing import Dict
from typing import Tuple
from typing import Union

from aiogram import types
from modules.operations.enums import OperationCreateCallback
from modules.operations.enums import OperationReceivedCallback
from modules.operations.enums import OperationType
from modules.operations.enums import RepeatType
from modules.operations.schemas import Operation


def strip_string(text: str) -> str:
    return text.replace(',', '').strip()


def get_weekday(time: str) -> list:
    base_days = {
        'понедельник': 0,
        'вторник': 1,
        'сред': 2,
        'четверг': 3,
        'пятниц': 4,
        'суббот': 5,
        'воскресень': 6,
    }
    return [
        next(iter([base_days[j] for j in base_days if x.find(j) != -1]))
        for x in time.split()
        if len([j for j in base_days if x.find(j) != -1]) != 0
    ]


def get_operation_regularity(text: str) -> Dict[str, Union[str, list]]:
    day_match = re.match(r'^(?P<intensive>\S.* день)', text)
    week_match = re.match(r'^(?P<intensive>\S.* неделю) (?P<at>в|во) (?P<time>\S.*)', text)
    week_other_match = re.match(r'^(каждый|каждую|каждое) (\D+)(,| |и)*$', text)
    month_patterns = [
        r'^(каждое) (\S.*) (числа|число)',
        r'^(?P<intensive>\S.* месяц) (\S.*) (числа|число)',
    ]
    month_matches = list(filter(None, [re.match(x, text) for x in month_patterns]))

    if day_match is not None:
        return {'type': 'every_day', 'days': []}
    elif week_match is not None:
        intensive, at, time = week_match.groups()
        return {'type': 'every_week', 'days': get_weekday(time)}
    elif len(month_matches) > 0:
        _, time, *_ = next(iter(month_matches)).groups()
        days = [
            'last' if strip_string(x).find('последн') != -1 else int(strip_string(x))
            for x in time.split()
            if strip_string(x).isdigit() or strip_string(x).find('последн') != -1
        ]
        return {'type': 'every_month', 'days': days}
    elif week_other_match is not None:
        intensive, time, _ = week_other_match.groups()
        return {'type': 'every_week', 'days': get_weekday(time)}


async def get_received_amount_markup(operation_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            '✅ Получил',
            callback_data=OperationReceivedCallback.full(operation_id),
        ),
        types.InlineKeyboardButton(
            '⚠️ Получил не всю сумму',
            callback_data=OperationReceivedCallback.partial(operation_id),
        ),
        types.InlineKeyboardButton(
            '❌ Не получил',
            callback_data=OperationReceivedCallback.none_received(operation_id),
        ),
    )
    return markup


async def get_operation_approved_markup(operation_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            '✅ Все правильно',
            callback_data=OperationCreateCallback.correct(operation_id),
        ),
        types.InlineKeyboardButton(
            '❌ Не правильно',
            callback_data=OperationCreateCallback.no(operation_id),
        ),
    )
    return markup


async def get_operation_text(  # noqa: CCR001
    operation: Operation,
    *,
    title: str = 'Подтвердите операцию',
) -> str:
    if operation.repeat_type != RepeatType.NO_REPEAT:  # TODO: Refactor
        repeat_days_text = ', '.join(list(map(str, operation.repeat_days)))
        repeat_at_days = (
            f'каждый {repeat_days_text} день'
            if operation.repeat_type != RepeatType.EVERY_DAY
            else ''
        )
        repeat_at = f'🔄 Повторять: {operation.repeat_type.get_translation()} {repeat_at_days}\n'
    else:
        repeat_at = '🔄 Повторять: Никогда\n'
    operation_type = '☺️' if operation.operation_type == OperationType.INCOME else '🥲'
    if operation.operation_type == OperationType.INCOME:
        received_amount = '⚠️ Получено'
    else:
        received_amount = '⚠️ Оплачено'
    received_amount += (
        f' {operation.received_amount}/{operation.amount}' if operation.received_amount else ''
    )
    return (
        f'<b>{title}:</b>\n\n'
        f'💰 Сумма: {operation.amount} {operation.currency.value.upper()}\n'
        f'{operation_type} Тип операции: {operation.operation_type.get_translation()}\n'
        f'{repeat_at}'
        f'💬 Описание: {operation.description}\n{received_amount}\n'
    )


async def get_current_month_period() -> Tuple[datetime.datetime, datetime.datetime]:
    now = datetime.datetime.now()
    max_days = calendar.monthrange(now.year, now.month)[1]
    date_from = datetime.datetime(now.year, now.month, 1)
    date_to = datetime.datetime(now.year, now.month, max_days)
    return date_from, date_to


def round_amount(amount: any, symbols: int) -> float:
    return round(float(amount), symbols)
