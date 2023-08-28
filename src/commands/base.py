import abc
from typing import List, Type


class Command:
    commands: List[Type['Command']] = []
    command_name: str

    @classmethod
    @abc.abstractmethod
    async def run(cls: Type['Command']) -> None:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        Command.commands.append(cls)
