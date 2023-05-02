from aiogram import executor
from config import dp
from database import database
from modules.analytics.views import *  # noqa: F403, F401
from modules.currencies.views import *  # noqa: F403, F401
from modules.helps.views import *  # noqa: F403, F401
from modules.operations.views import *  # noqa: F403, F401
from modules.users.views import *  # noqa: F403, F401


async def on_startup(*args, **kwargs) -> None:
    await database.connect()


async def on_shutdown(*args, **kwargs) -> None:
    await database.disconnect()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
