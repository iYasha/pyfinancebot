import calendar
import datetime
import re
from typing import Awaitable, Callable, Dict, List, Optional, Sequence, Tuple, Union, get_args

from aiogram import types
from aiogram.dispatcher import filters
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from config import dp, settings
from modules.operations.enums import (
    BackScreenType,
    CategoryCallback,
    ExpenseCategoryEnum,
    IncomeCategoryEnum,
    OperationAllCallback,
    OperationCreateCallback,
    OperationReceivedCallback,
    OperationType,
    RepeatType,
)
from modules.operations.schemas import Operation, OperationImport


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


def get_operation_regularity(text: str) -> Optional[Dict[str, Union[str, list]]]:
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
    return None


async def get_received_amount_markup(
    operation_id: int,
    is_income: bool = True,
) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    received_text = 'Получил' if is_income else 'Оплатил'
    markup.add(
        types.InlineKeyboardButton(
            f'✅ {received_text}',
            callback_data=OperationReceivedCallback.full(operation_id),
        ),
        types.InlineKeyboardButton(
            f'⚠️ {received_text} не всю сумму',
            callback_data=OperationReceivedCallback.partial(operation_id),
        ),
        types.InlineKeyboardButton(
            f'❌ Не {received_text}',
            callback_data=OperationReceivedCallback.none_received(operation_id),
        ),
    )
    return markup


def get_expense_categories_markup(
    operation_id: int,
    possible_categories: List[ExpenseCategoryEnum],
    markup: Optional[types.InlineKeyboardMarkup] = None,
) -> types.InlineKeyboardMarkup:
    if markup is None:
        markup = types.InlineKeyboardMarkup()
    for category in possible_categories:
        markup.add(
            types.InlineKeyboardButton(
                category.get_translation(),
                callback_data=OperationCreateCallback.correct(
                    operation_id,
                    category.value,
                    OperationType.EXPENSE,
                ),
            ),
        )
    markup.add(
        types.InlineKeyboardButton(
            '🔽 Другая категория',
            callback_data=CategoryCallback.more(operation_id),
        ),
    )
    return markup


def get_income_categories_markup(
    operation_id: int,
    markup: Optional[types.InlineKeyboardMarkup] = None,
) -> types.InlineKeyboardMarkup:
    if markup is None:
        markup = types.InlineKeyboardMarkup()
    for category in list(IncomeCategoryEnum):
        markup.add(
            types.InlineKeyboardButton(
                category.get_translation(),
                callback_data=OperationCreateCallback.correct(
                    operation_id,
                    category.value,
                    OperationType.INCOME,
                ),
            ),
        )
    return markup


def get_future_operation_markup(
    operations: Sequence[OperationImport],
    back_screen_type: BackScreenType = BackScreenType.FUTURE,
) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for operation in operations:
        op_type = '+' if operation.operation_type == OperationType.INCOME else '-'
        category_smile = '📝' if operation.category is None else operation.category.get_translation().split(' ')[0]
        markup.add(
            types.InlineKeyboardButton(
                f'{category_smile} {operation.description} | '
                f'{op_type}{operation.amount} {operation.currency.value.upper()} | '
                f'({operation.created_at.strftime("%d.%m.%Y")})',
                callback_data=OperationAllCallback.detail(operation.id, 1, back_screen_type),
            ),
        )
    return markup


def get_operations_markup(
    operations: Sequence[Operation],
    page: int,
    back_screen_type: BackScreenType = BackScreenType.ALL_OPERATIONS,
) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for operation in operations:
        op_type = '+' if operation.operation_type == OperationType.INCOME else '-'
        category_smile = '📝' if operation.category is None else operation.category.get_translation().split(' ')[0]
        markup.add(
            types.InlineKeyboardButton(
                f'{category_smile} {operation.description} | '
                f'{op_type}{operation.received_amount} {operation.currency.value.upper()}',
                callback_data=OperationAllCallback.detail(operation.id, page, back_screen_type),
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
    is_regular_operation: bool = False,
) -> List[types.InlineKeyboardButton]:
    from_range, to_range = get_pagination_range(current_page, max_page, min_page)

    markup = []
    for btn_no, page in enumerate(range(from_range, to_range + 1)):
        text = str(page)
        data = page

        if btn_no == 0 and page != min_page:
            text, data = '◀️', min_page
        elif btn_no + 1 == settings.PAGINATION_MAX_PAGES and page != max_page:
            text, data = '▶️', max_page
        elif page == current_page:
            text, data = f'[{page}]', page

        markup.append(
            types.InlineKeyboardButton(
                text=text,
                callback_data=OperationAllCallback.pagination(data, is_regular_operation),
            ),
        )

    return markup


def get_operation_text(
    operation: Operation,
    *,
    title: str = 'Подтвердите операцию',
    is_regular: bool = False,
) -> str:
    if operation.repeat_type != RepeatType.NO_REPEAT:
        repeat_days_text = ', '.join(map(str, operation.repeat_days))  # type: ignore[arg-type]
        repeat_at_days = f'каждый {repeat_days_text} день' if operation.repeat_type != RepeatType.EVERY_DAY else ''
        repeat_at = f'🔄 Повторять: {operation.repeat_type.get_translation()} {repeat_at_days}\n'
    else:
        repeat_at = '🔄 Повторять: Никогда\n'
    operation_type = '☺️' if operation.operation_type == OperationType.INCOME else '🥲'
    if is_regular:
        received_amount = ''
    elif operation.operation_type == OperationType.INCOME:
        received_amount = '⚠️ Получено'
    else:
        received_amount = '⚠️ Оплачено'
    received_amount += f' {operation.received_amount}/{operation.amount}' if operation.received_amount else ''
    category = f'📂 Категория: {operation.category.get_translation()}\n' if operation.category else ''
    if operation.monobank_account_id:
        integration_mark = '🔗 Интеграция: Monobank\n'
    else:
        integration_mark = ''
    return (
        f'<b>{title}:</b>\n\n'
        f'💰 Сумма: {operation.amount} {operation.currency.value.upper()}\n'
        f'{operation_type} Тип операции: {operation.operation_type.get_translation()}\n{category}'
        f'🗓 Дата создания: {operation.created_at.strftime("%Y-%m-%d %H:%M")}\n'
        f'{repeat_at}'
        f'💬 Описание: {operation.description}\n{received_amount}\n' + integration_mark
    )


async def get_current_month_period() -> Tuple[datetime.datetime, datetime.datetime]:
    now = datetime.datetime.now()
    max_days = calendar.monthrange(now.year, now.month)[1]
    date_from = datetime.datetime(now.year, now.month, 1)
    date_to = datetime.datetime(now.year, now.month, max_days)
    return date_from, date_to


async def get_current_day_period() -> Tuple[datetime.datetime, datetime.datetime]:
    now = datetime.datetime.now()
    return (
        datetime.datetime(now.year, now.month, now.day, 0, 0, 0),
        datetime.datetime(now.year, now.month, now.day, 23, 59, 59),
    )


def round_amount(amount: Union[str, int, float], symbols: int) -> float:
    return round(float(amount), symbols)


def get_operation_detail_markup(
    operation_id: int,
    page: int,
    back_type: BackScreenType,
) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    back_callback_data: Optional[str]
    if back_type in (BackScreenType.ALL_OPERATIONS, BackScreenType.REGULAR):
        back_callback_data = OperationAllCallback.pagination(
            page,
            is_regular_operation=back_type == BackScreenType.REGULAR,
        )
    else:
        back_callback_data = back_type.get_command()
    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад',
            callback_data=back_callback_data,
        ),
        types.InlineKeyboardButton(
            '❌ Удалить',
            callback_data=OperationAllCallback.delete(operation_id, page, back_type),
        ),
    )
    return markup


def get_other_categories(
    operation_id: int,
    categories: List[str],
    markup: types.InlineKeyboardMarkup,
) -> types.InlineKeyboardMarkup:
    for category in list(ExpenseCategoryEnum):
        if category in categories:
            continue
        markup.add(
            types.InlineKeyboardButton(
                category.get_translation(),
                callback_data=OperationCreateCallback.correct(
                    operation_id,
                    category.value,
                    OperationType.EXPENSE,
                ),
            ),
        )
    return markup


def get_message_handler(
    back_type: BackScreenType,
) -> Callable[[types.CallbackQuery], Awaitable[None]]:
    command_name = back_type.get_command()
    for handler in dp.message_handlers.handlers:
        handler_filter = next(
            filter(lambda x: isinstance(x.filter, filters.builtin.Command), handler.filters),
        )
        if (
            handler_filter is None
            or command_name not in handler_filter.filter.commands
            or types.CallbackQuery not in get_args(handler.spec.annotations['data'])
        ):
            continue
        return handler.handler
    raise ValueError(f'Handler for command {command_name} not found')


def get_cancel_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup()
    markup.add(KeyboardButton('❌ Отмена'))
    return markup


def format_report_diff(current_spending: float, prev_spending: float) -> str:
    diff = current_spending - prev_spending
    return f'{diff:+}'


def get_report_text(report: Dict[str, float], prev_report: Dict[str, float], title: str) -> str:
    intersection = set(prev_report.keys()) - set(report.keys())
    spending_categories = '\n\n'.join(
        [
            f'{ExpenseCategoryEnum(category).get_translation()} - <b>{report[category]:,}</b> грн.'.replace(
                ',',
                ' ',
            )
            + (
                f' (<code>{format_report_diff(report[category], prev_report[category])}</code>)'
                if category in prev_report
                else ''
            )
            for category in report
        ],
    )
    if len(intersection) > 0:
        spending_categories += '\n\n' + '\n\n'.join(
            [
                f'{ExpenseCategoryEnum(category).get_translation()} - <b>0</b> грн. '
                f'(<code>{format_report_diff(0, prev_report[category])}</code>)'.replace(',', ' ')
                for category in intersection
            ],
        )
    return f'<b>{title}:</b>\n\n{spending_categories}'
