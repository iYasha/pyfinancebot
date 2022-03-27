from core.config import settings
from aiogram import types

from crud.users import UserCRUD
import schemas
import enums


@settings.dp.message_handler(commands=[enums.Command.START])
async def authorization(message: types.Message):
    user_data = schemas.UserCreateSchema(
        chat_id=message.chat.id,
        first_name=message.chat.first_name,
        last_name=message.chat.last_name,
        username=message.chat.username
    )
    user: schemas.UserSchema = await UserCRUD.create_or_get(user_data)
    await settings.bot.send_message(user.chat_id, text='Welcome')
