from aiogram import types
from pydantic import ValidationError
from asyncpg.exceptions import ForeignKeyViolationError

from core.config import settings
from aiogram import types
import re

import crud
import schemas
import enums
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
                operation_type=enums.OperationType.get_operation_type(amount),
                description=description,
                repeat_type=time['type'],
                repeat_days=time['days'],
                is_approved=False,
            )
        elif operation_add is not None:
            amount, currency, description = re.match(settings.OPERATION_ADD_REGEX_PATTERN, message.text).groups()
            amount = amount.replace(' ', '').strip()
            operation_create = schemas.OperationCreateSchema(
                user_id=message.chat.id,
                amount=amount,
                operation_type=enums.OperationType.get_operation_type(amount),
                description=description,
                repeat_type=enums.RepeatType.NO_REPEAT,
                is_approved=False,
            )
        if operation_create:
            operation: schemas.OperationInDBSchema = await crud.OperationCRUD.create(operation_create)
            if operation.repeat_type != enums.RepeatType.NO_REPEAT:
                repeat_days_text = ', '.join(list(map(str, operation.repeat_days)))
                repeat_at = f'Повторять: {operation.repeat_type.get_translation()} каждый {repeat_days_text} день\n'
            else:
                repeat_at = 'Повторять: Никогда\n'
            text = f'Сумма: {operation.amount} грн.\n' \
                   f'Тип операции: {operation.operation_type.get_translation()}\n' \
                   f'{repeat_at}' \
                   f'Описание: {operation.description}\n'
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(
                    'Все правильно',
                    callback_data=enums.OperationCreateCallback.correct(operation.id)
                ),
                types.InlineKeyboardButton(
                    'Не правильно',
                    callback_data=enums.OperationCreateCallback.no(operation.id)
                ),
            )

            await settings.bot.send_message(
                message.chat.id,
                text=text,
                reply_markup=markup
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
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )
    elif callback_query.data.startswith(enums.OperationCreateCallback.NO):
        operation_id = callback_query.data.replace(f'{enums.OperationCreateCallback.NO}_', '')
        await crud.OperationCRUD.destroy(operation_id)
        await settings.bot.edit_message_text(
            text=f'{callback_query.message.html_text}\n❌ Операция не создана',
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )

