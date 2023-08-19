from calendar import monthrange
from datetime import datetime
from datetime import timedelta
from typing import Tuple
from typing import Type

from commands.base import Command
from config import bot
from config import settings
from modules.companies.services import CompanyService
from modules.operations.services import OperationService

from sdk import utils


class BaseReport:
    message_title: str

    @classmethod
    def get_range(cls) -> Tuple[datetime, datetime]:
        raise NotImplementedError

    @classmethod
    def get_prev_range(cls) -> Tuple[datetime, datetime]:
        raise NotImplementedError

    @classmethod
    async def run(cls: Type['BaseReport']) -> None:
        date_from, date_to = cls.get_range()
        for company in await CompanyService.get_all_companies():
            operations = await OperationService.get_stats_by_categories(
                date_from=date_from,
                date_to=date_to,
                company_id=company.id,
            )

            if not operations:
                continue

            prev_date_from, prev_date_to = cls.get_prev_range()
            prev_operations = await OperationService.get_stats_by_categories(
                date_from=prev_date_from,
                date_to=prev_date_to,
                company_id=company.id,
            )

            for user in company.participants:
                await bot.send_message(
                    user.chat_id,
                    text=utils.get_report_text(
                        operations,
                        prev_operations,
                        title=cls.message_title,
                    ),
                    parse_mode=settings.PARSE_MODE,
                )


class SendWeeklyReport(BaseReport, Command):
    command_name = 'send_weekly_report'
    message_title = 'Еженедельный отчет'

    @classmethod
    def get_range(cls) -> Tuple[datetime, datetime]:
        now = datetime.now() - timedelta(days=1)
        date_from = (now - timedelta(days=now.weekday())).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        date_to = (date_from + timedelta(days=6)).replace(hour=23, minute=59, second=59)
        return date_from, date_to

    @classmethod
    def get_prev_range(cls) -> Tuple[datetime, datetime]:
        now = datetime.now() - timedelta(days=1)
        date_from = (now - timedelta(days=now.weekday() + 7)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        date_to = (date_from + timedelta(days=6)).replace(hour=23, minute=59, second=59)
        return date_from, date_to


class SendMonthlyReport(BaseReport, Command):
    command_name = 'send_monthly_report'
    message_title = 'Ежемесячный отчет'

    @classmethod
    def get_range(cls) -> Tuple[datetime, datetime]:
        now = datetime.now() - timedelta(days=1)
        date_from = datetime(now.year, now.month, 1, 0, 0, 0)
        date_to = datetime(now.year, now.month, monthrange(now.year, now.month)[1], 23, 59, 59)
        return date_from, date_to

    @classmethod
    def get_prev_range(cls) -> Tuple[datetime, datetime]:
        now = datetime.now() - timedelta(days=1)
        date_from = datetime(now.year, now.month - 1, 1, 0, 0, 0)
        date_to = datetime(
            now.year,
            date_from.month,
            monthrange(now.year, date_from.month)[1],
            23,
            59,
            59,
        )
        return date_from, date_to
