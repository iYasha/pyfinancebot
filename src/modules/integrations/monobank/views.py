from aiogram import types

from config import bot, dp, settings
from modules.helps.enums import Command
from modules.integrations.enums import AvailableIntegration
from modules.integrations.monobank.exceptions import MonobankException
from modules.integrations.monobank.services import MonobankIntegrationService, MonobankService
from sdk.decorators import SelectCompanyRequired, error_handler_decorator


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(AvailableIntegration.MONOBANK),
)
@error_handler_decorator
async def monobank_integration(callback_query: types.CallbackQuery) -> None:
    markup = types.InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    '🔙 Назад',
                    callback_data=Command.INTEGRATIONS,
                ),
            ],
        ],
    )
    chat_id = callback_query.message.chat.id
    if await MonobankIntegrationService.is_integrated(chat_id, settings.SELECTED_COMPANIES[chat_id]):
        # TODO: Add ability to turn off/on integration for specific accounts
        await bot.edit_message_text(
            text="Вы уже подключили Monobank",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode=settings.PARSE_MODE,
            reply_markup=markup,
        )
    else:
        text = (
            'Для интеграции с Monobank нужно создать токен. Чтобы создать токен, нужно:\n'
            '1. Перейти по ссылке: https://api.monobank.ua/\n'
            '2. Отсканировать QR-код с помощью телефона или приложения monobank\n'
            '3. Подтвердить вход в приложении Monobank\n'
            '4. Активировать токен на сайте\n'
            '5. Отправить токен командой /set_monobank_token TOKEN. Где TOKEN - ваш токен'
        )
        await bot.edit_message_text(
            text=text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode=settings.PARSE_MODE,
            reply_markup=markup,
        )


@dp.message_handler(commands=[Command.SET_MONOBANK_TOKEN])
@SelectCompanyRequired
@error_handler_decorator
async def set_monobank_token(message: types.Message) -> None:
    token = message.get_args().strip()
    chat_id = message.chat.id
    company_id = settings.SELECTED_COMPANIES[chat_id]
    error_message = 'Неверный формат токена или токен не указан.'
    if not token:
        await bot.send_message(
            message.chat.id,
            text=error_message,
        )
        return
    try:
        client_info = await MonobankService(token).get_client_info()
    except MonobankException:
        await bot.send_message(
            message.chat.id,
            text=error_message,
        )
        return
    await MonobankIntegrationService.set_integration_key(chat_id, company_id, token)
    text = f'Поздравляю {client_info.name}! Интеграция с Monobank успешно завершена.'
    await bot.send_message(message.chat.id, text=text)
