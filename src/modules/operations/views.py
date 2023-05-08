import datetime
from typing import Union

from aiogram import types
from config import bot
from config import dp
from config import settings
from modules.helps.enums import Command
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


@dp.message_handler(commands=[Command.OPERATIONS])
@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationAllCallback.PAGINATION),
)
@error_handler_decorator
async def get_operations(data: Union[types.Message, types.CallbackQuery]) -> None:
    if isinstance(data, types.Message):
        page = 1
        message = data
    else:
        page = int(data.data.replace(f'{OperationAllCallback.PAGINATION}_', ''))
        message = data.message
        prev_page_buttons = next(
            filter(lambda x: len(x) > 1, message.reply_markup.inline_keyboard),
            [],
        )
        message_is_not_modified = bool(
            next(filter(lambda x: x.text == f'[{page}]', prev_page_buttons), False),
        )
        if message_is_not_modified:
            return

    paginated_operations = await OperationService.get_operations(page)
    if paginated_operations.total_count == 0:
        await message.answer('Операции не найдены')
        return

    markup = await utils.get_operations_markup(paginated_operations.results, page)
    markup.row(
        *utils.get_pagination_markup(page, max_page=paginated_operations.page_count),
    )

    if isinstance(data, types.CallbackQuery):
        await bot.edit_message_text(
            text='Операции',
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=markup,
        )
        return

    await bot.send_message(message.chat.id, text='Операции', reply_markup=markup)


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationAllCallback.DETAIL),
)
@error_handler_decorator
async def get_operation_detail(callback_query: types.CallbackQuery) -> None:
    message = callback_query.message
    operation_id, page = map(
        int,
        callback_query.data.replace(f'{OperationAllCallback.DETAIL}_', '').split('_'),
    )
    operation = await OperationService.get_operation(operation_id)

    await bot.edit_message_text(
        text=await utils.get_operation_text(operation),
        chat_id=message.chat.id,
        message_id=message.message_id,
        parse_mode=settings.PARSE_MODE,
        reply_markup=utils.get_operation_detail_markup(operation_id, page),
    )


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(OperationAllCallback.DELETE),
)
@error_handler_decorator
async def delete_operation(callback_query: types.CallbackQuery) -> None:
    operation_id, page = map(
        int,
        callback_query.data.replace(f'{OperationAllCallback.DELETE}_', '').split('_'),
    )
    await OperationService.delete_operation(operation_id)

    count = await OperationService.get_operation_count()
    if count == 0:
        await bot.edit_message_text(
            text='✅ Операция успешно удалена!',
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
        )
        return

    callback_query.data = OperationAllCallback.pagination(page)
    await get_operations(callback_query)


@dp.message_handler(regexp=settings.OPERATION_REGEX_PATTERN)
@error_handler_decorator
async def create_operation(message: types.Message) -> None:
    operation_data = OperationService.parse_operation(message.text, message.chat.id)
    if not operation_data:
        return

    operation_data, possible_categories = operation_data
    operation: Operation = await OperationService.create_operation(operation_data)

    if operation.operation_type == OperationType.EXPENSE:
        categories = utils.get_expense_categories_markup(operation.id, possible_categories)
    else:
        categories = utils.get_income_categories_markup(operation.id)

    await bot.send_message(
        message.chat.id,
        text=await utils.get_operation_text(operation, title='Выберите категорию'),
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
            x[0]['callback_data'].replace(f'{OperationCreateCallback.CORRECT}_', '').split('_')[1:],
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
    received_amount = 0 or operation.received_amount
    await OperationService.update_operation(
        operation_id,
        OperationUpdate(received_amount=received_amount + amount),
    )
    received_amount_text = (
        f'⚠️ Получено {amount}/{operation.amount}'
        if operation.amount > amount
        else '✅ Сумма успешно сохранена'
    )
    await bot.edit_message_text(
        text=f'{message.reply_to_message.html_text}\n{received_amount_text}',
        parse_mode=settings.PARSE_MODE,
        chat_id=message.chat.id,
        message_id=message.reply_to_message.message_id,
    )
