from aiogram import types

from config import bot, dp, settings
from modules.companies.services import CompanyService
from modules.helps.enums import Command
from modules.users.schemas import UserCreate
from modules.users.services import UserService
from sdk.decorators import error_handler_decorator


@dp.message_handler(commands=[Command.START])
@error_handler_decorator
async def authorization(message: types.Message, **kwargs) -> None:
    invited = kwargs['command'].args
    user_data = UserCreate(
        chat_id=message.chat.id,
        first_name=message.chat.first_name,
        last_name=message.chat.last_name,
        username=message.chat.username,
    )
    user = await UserService.get_user(message.chat.id)
    if not user:
        await UserService.create_or_ignore(user_data)
        await bot.send_message(
            message.chat.id,
            text='🌟 Добро пожаловать! Для ознакомления с возможностями бота введите /help',
        )
    if invited:
        company_id, creator_id = invited.split('_')
        company = await CompanyService.get_company(company_id, creator_id=creator_id)
        await CompanyService.add_participant(company_id, message.chat.id)
        await bot.send_message(
            chat_id=message.chat.id,
            text=f'🎉 Вы присоединились к компании "<b>{company.name}</b>"! '
            f'Для ознакомления с возможностями бота введите /help',
            parse_mode=settings.PARSE_MODE,
        )
    if user and not invited:
        await bot.send_message(
            chat_id=message.chat.id,
            text='Вы уже зарегистрированы! Для ознакомления с возможностями бота введите /help',
        )
