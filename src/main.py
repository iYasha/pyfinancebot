from core.config import settings  # noqa
from core.database import database
from aiogram import executor
from views import *  # noqa


async def on_startup(*args, **kwargs) -> None:
    await database.connect()


async def on_shutdown(*args, **kwargs) -> None:
    await database.disconnect()


if __name__ == '__main__':
    executor.start_polling(settings.dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
