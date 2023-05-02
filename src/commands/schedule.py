from datetime import datetime
from typing import List
from typing import Optional
from typing import Type

from commands.base import Command
from commands.currencies import FetchCurrency
from commands.operations import CreateRegularOperation, SendRegularOperationNotification
from croniter import croniter
from config import logger


class Job:
    def __init__(self, command: Type[Command], cron_pattern: Optional[str] = None) -> None:
        self.command = command
        self.cron_pattern = cron_pattern

    def every_hour(self) -> 'Job':
        self.cron_pattern = '0 * * * *'
        return self

    def every_day(self) -> 'Job':
        self.cron_pattern = '0 0 * * *'
        return self

    def every_minute(self) -> 'Job':
        self.cron_pattern = '* * * * *'
        return self

    def cron(self, cron_pattern: str) -> 'Job':
        self.cron_pattern = cron_pattern
        return self

    def is_due(self, now: datetime) -> bool:
        if self.cron_pattern is None:
            return False
        return croniter.match(self.cron_pattern, now)


class Scheduler:
    @classmethod
    def command(cls: Type['Scheduler'], command: Type[Command]) -> Job:
        return Job(command)


class Schedule(Command):
    command_name = 'schedule'
    schedule: Scheduler = Scheduler

    @classmethod
    async def get_jobs(cls: Type['Schedule']) -> List[Job]:
        return [
            cls.schedule.command(FetchCurrency).cron('0 8 * * *'),
            cls.schedule.command(CreateRegularOperation).cron('0 9 * * *'),
        ]

    @classmethod
    async def run(cls: Type['Schedule']) -> None:
        now = datetime.now()
        for job in await cls.get_jobs():
            if job.is_due(now):
                logger.info(f'Running {job.command.command_name} command')
                await job.command.run()
