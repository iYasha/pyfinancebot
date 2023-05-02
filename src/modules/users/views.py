from aiogram import types
from config import bot
from config import dp
from modules.helps.enums import Command
from modules.users.schemas import UserCreate
from modules.users.services import UserService

from sdk.exceptions.handler import error_handler_decorator


@dp.message_handler(commands=[Command.START])
@error_handler_decorator
async def authorization(message: types.Message, **kwargs) -> None:
    user_data = UserCreate(
        chat_id=message.chat.id,
        first_name=message.chat.first_name,
        last_name=message.chat.last_name,
        username=message.chat.username,
    )
    await UserService.create_or_ignore(user_data)
    await bot.send_message(message.chat.id, text='Welcome')
