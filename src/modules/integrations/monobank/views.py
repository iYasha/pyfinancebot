from aiogram import types

from config import bot, dp, settings
from modules.helps.enums import Command
from modules.integrations.enums import AvailableIntegration
from modules.integrations.monobank.enums import MonobankCallback
from modules.integrations.monobank.exceptions import MonobankException
from modules.integrations.monobank.services import MonobankIntegrationService, MonobankService
from sdk.decorators import SelectCompanyRequired, error_handler_decorator, transaction_decorator


async def send_account_list(chat_id: int, message_id: int) -> None:
    """
    Update message with account list
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    accounts = await MonobankIntegrationService.get_accounts(chat_id, settings.SELECTED_COMPANIES[chat_id])
    for account in accounts:
        button = types.InlineKeyboardButton(
            f"{'🟢' if account.is_active else '🔴'} {account.name}",
            callback_data=MonobankCallback.change_account_status(account.id),
        )
        markup.row(button)
    markup.row(
        types.InlineKeyboardButton(
            '🚫 Отключить интеграцию с Monobank',
            callback_data=MonobankCallback.DISABLE,
        ),
    )
    markup.row(
        types.InlineKeyboardButton(
            '🔙 Назад',
            callback_data=Command.INTEGRATIONS,
        ),
    )

    await bot.edit_message_text(
        text="Интеграция: <b>Monobank</b>\n\n"
        "Вы можете отключить интеграцию с Monobank или конкретный счет нажав на него.\n\n"
        "<i>Если вы открыли счет/карту в Monobank после интеграции, "
        "он автоматически появится в списке после проведения транзакции с ним.</i>",
        chat_id=chat_id,
        message_id=message_id,
        parse_mode=settings.PARSE_MODE,
        reply_markup=markup,
    )


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(AvailableIntegration.MONOBANK),
)
@SelectCompanyRequired
@error_handler_decorator
async def monobank_integration(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    integration_key = await MonobankIntegrationService.get_integration_key(
        chat_id,
        settings.SELECTED_COMPANIES[chat_id],
    )
    if integration_key:
        await send_account_list(chat_id, callback_query.message.message_id)
    else:
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
    await bot.answer_callback_query(callback_query.id)


@dp.message_handler(commands=[Command.SET_MONOBANK_TOKEN])
@SelectCompanyRequired
@error_handler_decorator
@transaction_decorator
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
    monobank_service = MonobankService(token)
    try:
        client_info = await monobank_service.get_client_info()
    except MonobankException:
        await bot.send_message(
            message.chat.id,
            text=error_message,
        )
        return
    webhook_secret = await MonobankIntegrationService.set_integration_key(chat_id, company_id, token)
    await MonobankIntegrationService.set_accounts(chat_id, company_id, client_info)
    await monobank_service.set_webhook(webhook_secret)
    text = f'Поздравляю {client_info.name}! Интеграция с Monobank успешно завершена.'
    await bot.send_message(message.chat.id, text=text)


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith(MonobankCallback.CHANGE_ACCOUNT_STATUS),
)
@SelectCompanyRequired
@error_handler_decorator
async def change_account_status(callback_query: types.CallbackQuery) -> None:
    account_id = callback_query.data.split(':')[-1]
    chat_id = callback_query.message.chat.id
    company_id = settings.SELECTED_COMPANIES[chat_id]
    await MonobankIntegrationService.change_account_status(chat_id, company_id, account_id)
    await send_account_list(chat_id, callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(
    lambda c: c.data == MonobankCallback.DISABLE,
)
@SelectCompanyRequired
@error_handler_decorator
@transaction_decorator
async def disable_monobank_integration(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    company_id = settings.SELECTED_COMPANIES[chat_id]
    await MonobankIntegrationService.remove_integration(chat_id, company_id)
    await MonobankIntegrationService.delete_accounts(chat_id, company_id)
    await bot.send_message(
        chat_id,
        text='Интеграция с Monobank успешно отключена.',
    )
    await bot.answer_callback_query(callback_query.id)
