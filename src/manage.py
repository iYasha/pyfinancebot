import argparse
import asyncio
from typing import Type

from commands.base import Command
from config import logger
from database import database


async def startup() -> None:
    await database.connect()


async def shutdown() -> None:
    await database.disconnect()


class ConsoleManager:
    @classmethod
    async def execute_command(cls: Type['ConsoleManager'], command_name: str) -> None:
        if command_name is None:
            raise ValueError('Command name is required')

        command_instance: Command = next(
            filter(lambda command: command.command_name == command_name, Command.commands),
            None,
        )
        if command_instance is None:
            raise ValueError(f'Command {command_name} not found')

        await command_instance.run()


if __name__ == '__main__':
    # TODO: Use subparsers for commands https://docs.python.org/3/library/argparse.html#sub-commands
    argparse = argparse.ArgumentParser()
    argparse.add_argument(
        '-c',
        '--command',
        type=str,
        help='Run command',
        required=True,
    )
    args = argparse.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())
    try:
        loop.run_until_complete(ConsoleManager.execute_command(args.command))
    except Exception:
        logger.exception(f'Error executing command: {args.command}')
    loop.run_until_complete(shutdown())
