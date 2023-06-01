import datetime
from typing import Union

from aiogram import types
from config import bot
from config import dp
from config import settings
from modules.helps.enums import Command
from modules.operations.enums import BackScreenType
from modules.operations.enums import CategoryCallback
from modules.operations.enums import ExpenseCategoryEnum
from modules.operations.enums import IncomeCategoryEnum
from modules.operations.enums import OperationAllCallback
from modules.operations.enums import OperationCreateCallback
from modules.operations.enums import OperationReceivedCallback
from modules.operations.enums import OperationType
from modules.operations.schemas import Operation
from modules.operations.schemas import OperationUpdate
from modules.operations.services import OperationService

from sdk import utils
from sdk.exceptions.handler import error_handler_decorator
from sdk.exceptions.handler import select_company_required
from sdk.utils import get_message_handler


@dp.message_handler(commands=[Command.OPERATIONS, Command.REGULAR])
@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationAllCallback.PAGINATION),
)
@select_company_required
@error_handler_decorator
async def get_operations(data: Union[types.Message, types.CallbackQuery]) -> None:
    if isinstance(data, types.Message):
        is_regular_operations = data.text == f'/{Command.REGULAR}'
        page = 1
        message = data
        chat_id = data.chat.id
    else:
        page, is_regular_operations = map(
            int,
            data.data.replace(f'{OperationAllCallback.PAGINATION}_', '').split('_'),
        )
        is_regular_operations = bool(is_regular_operations)
        message = data.message
        is_message_modified = bool(
            [
                button
                for markup in message.reply_markup.inline_keyboard
                for button in markup
                if button.text == f'[{page}]'
                and button.callback_data.startswith(OperationAllCallback.PAGINATION)
            ],
        )
        if is_message_modified:
            return
        chat_id = message.chat.id

    back_screen_type = BackScreenType.ALL_OPERATIONS
    message_text = 'Операции'
    if is_regular_operations:
        back_screen_type = BackScreenType.REGULAR
        message_text = 'Регулярные операции'

    paginated_operations = await OperationService.get_operations(
        settings.SELECTED_COMPANIES[chat_id],
        page,
        is_regular_operation=is_regular_operations,
    )

    reply_markup = utils.get_operations_markup(
        paginated_operations.results,
        page,
        back_screen_type,
    )
    reply_markup.row(
        *utils.get_pagination_markup(
            page,
            max_page=paginated_operations.page_count,
            is_regular_operation=is_regular_operations,
        ),
    )

    if isinstance(data, types.CallbackQuery):
        await bot.edit_message_text(
            text=message_text,
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=reply_markup,
        )
        return

    await bot.send_message(message.chat.id, text=message_text, reply_markup=reply_markup)


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(Command.FUTURE),
)
@dp.message_handler(commands=[Command.FUTURE])
@select_company_required
@error_handler_decorator
async def get_future_operations(data: Union[types.Message, types.CallbackQuery]) -> None:
    if isinstance(data, types.Message):
        chat_id = data.chat.id
    else:
        chat_id = data.message.chat.id
    future_operations = await OperationService.get_future_operations(
        settings.SELECTED_COMPANIES[chat_id],
    )
    markup = utils.get_future_operation_markup(
        future_operations,
    )
    if isinstance(data, types.CallbackQuery):
        await bot.edit_message_text(
            chat_id=data.message.chat.id,
            message_id=data.message.message_id,
            text='Будущие операции',
            reply_markup=markup,
        )
    else:
        await bot.send_message(data.chat.id, text='Будущие операции', reply_markup=markup)


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationAllCallback.DETAIL),
)
@error_handler_decorator
async def get_operation_detail(callback_query: types.CallbackQuery) -> None:
    message = callback_query.message
    operation_id, page, back_type = callback_query.data.replace(
        f'{OperationAllCallback.DETAIL}_',
        '',
    ).split('_')
    operation_id = int(operation_id)
    page = int(page)
    operation = await OperationService.get_operation(operation_id)

    await bot.edit_message_text(
        text=utils.get_operation_text(operation, title='Детали операции'),
        chat_id=message.chat.id,
        message_id=message.message_id,
        parse_mode=settings.PARSE_MODE,
        reply_markup=utils.get_operation_detail_markup(
            operation_id,
            page,
            BackScreenType(back_type),
        ),
    )


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationAllCallback.DELETE),
)
@error_handler_decorator
async def delete_operation(callback_query: types.CallbackQuery) -> None:
    operation_id, page, back_type = callback_query.data.replace(
        f'{OperationAllCallback.DELETE}_',
        '',
    ).split('_')
    operation_id = int(operation_id)
    page = int(page)
    back_type = BackScreenType(back_type)
    operation = await OperationService.get_operation(operation_id)
    category_smile = (
        '📝' if operation.category is None else operation.category.get_translation().split(' ')[0]
    )
    op_type = '+' if operation.operation_type == OperationType.INCOME else '-'
    await bot.answer_callback_query(
        callback_query.id,
        text=f'🗑 Операция "{category_smile} {operation.description} | '
        f'{op_type}{operation.amount} {operation.currency.value.upper()}" удалена!',
    )
    await OperationService.delete_operation(operation_id)

    if back_type in (BackScreenType.REGULAR, BackScreenType.ALL_OPERATIONS):
        callback_query.data = OperationAllCallback.pagination(
            page,
            is_regular_operation=back_type == BackScreenType.REGULAR,
        )
        handler = get_operations
    else:
        handler = get_message_handler(back_type)
    await handler(callback_query)


@dp.message_handler(regexp=settings.OPERATION_REGEX_PATTERN)
@select_company_required
@error_handler_decorator
async def create_operation(message: types.Message) -> None:
    operation_data = OperationService.parse_operation(message.text, message.chat.id)
    if not operation_data:
        return

    operation_data, possible_categories = operation_data
    operation: Operation = await OperationService.create_operation(
        operation_data,
        company_id=settings.SELECTED_COMPANIES[message.chat.id],
    )

    if operation.operation_type == OperationType.EXPENSE:
        categories = utils.get_expense_categories_markup(operation.id, possible_categories)
    else:
        categories = utils.get_income_categories_markup(operation.id)

    await bot.send_message(
        message.chat.id,
        text=utils.get_operation_text(operation, title='Выберите категорию'),
        parse_mode=settings.PARSE_MODE,
        reply_markup=categories,
    )


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationCreateCallback.UNIQUE_PREFIX),
)
@error_handler_decorator
async def process_operation_create(callback_query: types.CallbackQuery) -> None:
    operation_text = callback_query.message.html_text
    if callback_query.data.startswith(OperationCreateCallback.CORRECT):
        data = callback_query.data.replace(f'{OperationCreateCallback.CORRECT}_', '').split('_')
        operation_id, operation_type, category_slug = int(data[0]), data[1], ('_'.join(data[2:]))
        category: Union[IncomeCategoryEnum, ExpenseCategoryEnum] = (
            IncomeCategoryEnum(category_slug)
            if operation_type == '+'
            else ExpenseCategoryEnum(category_slug)
        )
        await OperationService.approve_operation(operation_id, category)
        text_by_line = operation_text.split('\n')
        operation_text = '\n'.join(
            text_by_line[:4] + [f'📂 Категория: {category.get_translation()}'] + text_by_line[4:],
        )
        operation_text = f'{operation_text}\n✅ Операция успешно создана'

    elif callback_query.data.startswith(OperationCreateCallback.NO):
        operation_id = int(callback_query.data.replace(f'{OperationCreateCallback.NO}_', ''))
        await OperationService.delete_operation(operation_id)
        operation_text = f'{operation_text}\n❌ Операция не создана'

    await bot.edit_message_text(
        text=operation_text,
        parse_mode=settings.PARSE_MODE,
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(CategoryCallback.SHOW_MORE),
)
@error_handler_decorator
async def show_more_categories(callback_query: types.CallbackQuery) -> None:
    message = callback_query.message
    markup = message.reply_markup
    operation_id = int(callback_query.data.replace(f'{CategoryCallback.SHOW_MORE}_', ''))
    inline_keyboard = markup.inline_keyboard
    inline_keyboard.pop()
    categories = [
        '_'.join(
            x[0]['callback_data'].replace(f'{OperationCreateCallback.CORRECT}_', '').split('_')[2:],
        )
        for x in inline_keyboard
    ]

    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=utils.get_other_categories(operation_id, categories, markup),
    )


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationReceivedCallback.UNIQUE_PREFIX),
)
@error_handler_decorator
async def process_operation_received(callback_query: types.CallbackQuery) -> None:
    if callback_query.data.startswith(OperationReceivedCallback.PARTIAL):
        await callback_query.message.reply(
            text='<b>Чтобы указать полученную сумму - сделайте reply этого сообщения с указанием суммы</b>',
            parse_mode=settings.PARSE_MODE,
        )
        return

    operation_text = callback_query.message.html_text

    if callback_query.data.startswith(OperationReceivedCallback.FULL):
        operation_id = int(callback_query.data.replace(f'{OperationReceivedCallback.FULL}_', ''))
        await OperationService.approve_operation(operation_id)
        operation_text = f'{operation_text}\n✅ Операция успешно создана'
    elif callback_query.data.startswith(OperationReceivedCallback.NONE_RECEIVED):
        operation_text = f'{operation_text}\n❌ Сумма не получена'

    await bot.edit_message_text(
        text=operation_text,
        parse_mode=settings.PARSE_MODE,
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )


@dp.message_handler(
    lambda x: x.reply_to_message is not None
    and x.reply_to_message.reply_markup is not None
    and len(x.reply_to_message.reply_markup.inline_keyboard) > 0
    and len(x.reply_to_message.reply_markup.inline_keyboard[0]) > 0
    and x.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data.startswith(
        OperationReceivedCallback.UNIQUE_PREFIX,
    ),
)
@error_handler_decorator
async def reply_received_handler(message: types.Message) -> None:
    if message.date >= datetime.datetime(
        year=message.date.year,
        month=message.date.month,
        day=message.date.day,
        hour=23,
        minute=59,
    ):
        await message.reply(
            text='<b>Вы уже не можете изменить полученную сумму</b>',
            parse_mode=settings.PARSE_MODE,
        )
    operation_id = int(
        message.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data.replace(
            f'{OperationReceivedCallback.FULL}_',
            '',
        ),
    )
    if not message.text.strip().isdigit():
        await message.reply(text='<b>Нужно ввести число</b>', parse_mode=settings.PARSE_MODE)
    amount = int(message.text)
    if amount < 0:
        await message.reply(
            text='<b>Сумма должна быть больше 0</b>',
            parse_mode=settings.PARSE_MODE,
        )
    operation = await OperationService.get_operation(operation_id)
    received_amount = operation.received_amount or 0
    await OperationService.update_operation(
        operation_id,
        OperationUpdate(received_amount=received_amount + amount, is_approved=True),
    )
    received_text = 'Получено' if operation.operation_type == OperationType.INCOME else 'Оплачено'
    received_amount_text = (
        f'⚠️ {received_text} {amount}/{operation.amount}'
        if operation.amount > amount
        else '✅ Сумма успешно сохранена'
    )
    # TODO: Fix old amount "💰 Сумма: 310 UAH" in message
    await bot.edit_message_text(
        text=f'{message.reply_to_message.html_text}\n{received_amount_text}',
        parse_mode=settings.PARSE_MODE,
        chat_id=message.chat.id,
        message_id=message.reply_to_message.message_id,
    )
