import calendar
import datetime
import re
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from aiogram import types
from config import settings
from modules.operations.enums import OperationAllCallback
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


def get_operation_approved_markup(operation_id: int) -> types.InlineKeyboardMarkup:
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


async def get_operations_markup(
    operations: List[Operation],
    page: int,
) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for operation in operations:
        markup.add(
            types.InlineKeyboardButton(
                f'📝 {operation.description} - {operation.amount} {operation.currency.value.upper()}',
                callback_data=OperationAllCallback.detail(operation.id, page),
            ),
        )
    return markup


def get_pagination_range(
    current_page: int = 1,
    max_page: int = 1,
    min_page: int = 1,
) -> Tuple[int, int]:

    if max_page < settings.PAGINATION_MAX_PAGES:
        return min_page, max_page

    middle = (settings.PAGINATION_MAX_PAGES - 1) // 2
    from_range = current_page - middle
    to_range = current_page + middle

    if from_range < min_page:
        from_range = min_page
    if to_range > max_page:
        to_range = max_page
    if to_range < settings.PAGINATION_MAX_PAGES:
        to_range = settings.PAGINATION_MAX_PAGES
    if from_range > max_page - settings.PAGINATION_MAX_PAGES:
        from_range = max_page - settings.PAGINATION_MAX_PAGES + 1

    return from_range, to_range


def get_pagination_markup(
    current_page: int = 1,
    max_page: int = 1,
    min_page: int = 1,
) -> List[types.InlineKeyboardButton]:

    from_range, to_range = get_pagination_range(current_page, max_page, min_page)

    markup = []
    for btn_no, page in enumerate(range(from_range, to_range + 1)):
        text = str(page)
        data = page

        if btn_no == 0 and page != min_page:
            text, data = '<', min_page
        elif btn_no + 1 == settings.PAGINATION_MAX_PAGES and page != max_page:
            text, data = '>', max_page
        elif page == current_page:
            text, data = f'[{page}]', page

        markup.append(
            types.InlineKeyboardButton(
                text=text,
                callback_data=OperationAllCallback.pagination(data),
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
        f'🗓 Дата создания: {operation.created_at.strftime("%Y-%m-%d %H:%M")}\n'
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


def get_operation_detail_markup(operation_id: int, page: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад',
            callback_data=OperationAllCallback.pagination(page),
        ),
        types.InlineKeyboardButton(
            '❌ Удалить',
            callback_data=OperationAllCallback.delete(operation_id, page),
        ),
    )
    return markup
