import abc
from typing import Type


class Command:
    commands = []
    command_name: str

    @classmethod
    @abc.abstractmethod
    async def run(cls: Type['Command']) -> None:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        Command.commands.append(cls)
