import datetime

from pydantic import ValidationError
from asyncpg.exceptions import ForeignKeyViolationError

from core.config import settings
from aiogram import types
import re

import crud
import schemas
import enums
from sdk import utils
from sdk.utils import get_operation_regularity


@settings.dp.message_handler(regexp=settings.OPERATION_REGEX_PATTERN)
async def create_operation(message: types.Message):
    try:
        operation_add = re.match(settings.OPERATION_ADD_REGEX_PATTERN, message.text)
        add_regular_operation = re.match(settings.OPERATION_REGULAR_REGEX_PATTERN, message.text)
        operation_create = None
        if add_regular_operation is not None:
            amount, currency, repeat_time, description = add_regular_operation.groups()
            time = await get_operation_regularity(repeat_time)
            # @TODO проработать логику, когда платеж не совершен, тогда нужно со следующего платежа вычесть разницу
            """
            Если это оплата за квартиру, то платеж обязательный
            
            Если это платеж наперед, то он является необязательным и в случае неоплаты
            может быть засчитан на следующий период
            """
            operation_create = schemas.OperationCreateSchema(
                user_id=message.chat.id,
                amount=amount,
                currency=enums.Currency.get(currency),
                operation_type=enums.OperationType.get_operation_type(amount),
                description=description,
                repeat_type=time['type'],
                repeat_days=time['days'],
                is_regular_operation=True,
            )
        elif operation_add is not None:
            amount, currency, description = re.match(settings.OPERATION_ADD_REGEX_PATTERN, message.text).groups()
            amount = amount.replace(' ', '').strip()
            operation_create = schemas.OperationCreateSchema(
                user_id=message.chat.id,
                amount=amount,
                currency=enums.Currency.get(currency),
                operation_type=enums.OperationType.get_operation_type(amount),
                description=description,
                repeat_type=enums.RepeatType.NO_REPEAT,
            )
        if operation_create:
            operation: schemas.OperationInDBSchema = await crud.OperationCRUD.create(operation_create)

            await settings.bot.send_message(
                message.chat.id,
                text=await utils.get_operation_text(operation),
                parse_mode=settings.PARSE_MODE,
                reply_markup=await utils.get_operation_approved_markup(operation.id)
            )
    except ValidationError as e:  # @TODO Нужно создать middleware для ошибок и переводить их
        await settings.bot.send_message(
            message.chat.id,
            text='\n'.join([f'{x["loc"][0]}: {x["msg"]}' for x in e.errors()])
        )
    except ForeignKeyViolationError:  # Юзер не зарегистрирован
        await settings.bot.send_message(
            message.chat.id,
            text='Для начала нужно зарегистрироваться /start'
        )


@settings.dp.callback_query_handler(lambda c: c.data and c.data.startswith(enums.OperationCreateCallback.UNIQUE_PREFIX))
async def process_operation_create(callback_query: types.CallbackQuery):
    if callback_query.data.startswith(enums.OperationCreateCallback.CORRECT):
        operation_id = callback_query.data.replace(f'{enums.OperationCreateCallback.CORRECT}_', '')
        await crud.OperationCRUD.update(operation_id, is_approved=True)
        await settings.bot.edit_message_text(
            text=f'{callback_query.message.html_text}\n✅ Операция успешно создана',
            parse_mode=settings.PARSE_MODE,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )
    elif callback_query.data.startswith(enums.OperationCreateCallback.NO):
        operation_id = callback_query.data.replace(f'{enums.OperationCreateCallback.NO}_', '')
        await crud.OperationCRUD.destroy(operation_id)
        await settings.bot.edit_message_text(
            text=f'{callback_query.message.html_text}\n❌ Операция не создана',
            parse_mode=settings.PARSE_MODE,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )


@settings.dp.callback_query_handler(lambda c: c.data and c.data.startswith(enums.OperationReceivedCallback.UNIQUE_PREFIX))
async def process_operation_received(callback_query: types.CallbackQuery):
    if callback_query.data.startswith(enums.OperationReceivedCallback.FULL):
        operation_id = callback_query.data.replace(f'{enums.OperationReceivedCallback.FULL}_', '')
        operation = await crud.OperationCRUD.get_by_id(obj_id=operation_id)
        await crud.OperationCRUD.update(operation_id, received_amount=operation.amount)
        await settings.bot.edit_message_text(
            text=f'{callback_query.message.html_text}\n✅ Сумма успешно сохранена',
            parse_mode=settings.PARSE_MODE,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )
    elif callback_query.data.startswith(enums.OperationReceivedCallback.PARTIAL):
        await callback_query.message.reply(
            text='<b>Чтобы указать полученную сумму - сделайте reply этого сообщения с указанием суммы</b>',
            parse_mode=settings.PARSE_MODE
        )
    elif callback_query.data.startswith(enums.OperationReceivedCallback.NONE_RECEIVED):
        await settings.bot.edit_message_text(
            text=f'{callback_query.message.html_text}\n❌ Сумма не получена',
            parse_mode=settings.PARSE_MODE,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )


@settings.dp.message_handler(
    lambda x:
    x.reply_to_message is not None and
    x.reply_to_message.reply_markup is not None and
    len(x.reply_to_message.reply_markup.inline_keyboard) > 0 and
    len(x.reply_to_message.reply_markup.inline_keyboard[0]) > 0 and
    x.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data.startswith(enums.OperationReceivedCallback.UNIQUE_PREFIX))
async def reply_received_handler(message: types.Message):
    try:
        # @TODO Протестировать когда тип операции расход
        if message.date >= datetime.datetime(
                year=message.date.year, month=message.date.month, day=message.date.day, hour=23, minute=59
        ):
            await message.reply(
                text='<b>Вы уже не можете изменить полученную сумму</b>',
                parse_mode=settings.PARSE_MODE
            )
        operation_id = message.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data.replace(
            f'{enums.OperationReceivedCallback.FULL}_', ''
        )
        if not message.text.strip().isdigit():
            await message.reply(
                text='<b>Нужно ввести число</b>',
                parse_mode=settings.PARSE_MODE
            )
        amount = int(message.text)
        if amount < 0:
            await message.reply(
                text='<b>Сумма должна быть больше 0</b>',
                parse_mode=settings.PARSE_MODE
            )
        operation = await crud.OperationCRUD.get_by_id(obj_id=operation_id)
        await crud.OperationCRUD.update(operation_id, received_amount=amount)
        received_amount_text = f'⚠️ Получено {amount}/{operation.amount}' if operation.amount > amount else '✅ Сумма успешно сохранена'
        await settings.bot.edit_message_text(
            text=f'{message.reply_to_message.html_text}\n{received_amount_text}',
            parse_mode=settings.PARSE_MODE,
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id
        )
    except Exception as e:
        print(e)
        await message.reply(
            text='<b>Непредвиденная ошибка!</b>\n\n'
                 'Попробуйте позже или напишите в поддержку',
            parse_mode=settings.PARSE_MODE
        )

