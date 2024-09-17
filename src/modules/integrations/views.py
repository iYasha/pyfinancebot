from typing import Union

from aiogram import types

from config import bot, dp
from modules.helps.enums import Command
from modules.integrations.enums import AvailableIntegration
from sdk.decorators import SelectCompanyRequired, error_handler_decorator


@dp.message_handler(commands=[Command.INTEGRATIONS])
@dp.callback_query_handler(
    lambda c: c.data and c.data == Command.INTEGRATIONS,
)
@SelectCompanyRequired
@error_handler_decorator
async def get_available_integrations(data: Union[types.Message, types.CallbackQuery]) -> None:
    if isinstance(data, types.CallbackQuery):
        message = data.message
    else:
        message = data
    text = (
        'С помощью интеграций вы можете автоматически добавлять операции в вашу компанию.\n'
        'Интеграция происходит с выбранной компанией. Проверить какая компания выбрана можно командой /companies\n'
        'Чтобы начать интеграцию или изменить настройки интеграции выберите сервис:'
    )
    markup = types.InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    'Monobank',
                    callback_data=AvailableIntegration.MONOBANK.value,
                ),
            ],
        ],
    )
    if isinstance(data, types.CallbackQuery):
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=text,
            reply_markup=markup,
        )
    else:
        await bot.send_message(message.chat.id, text=text, reply_markup=markup)
