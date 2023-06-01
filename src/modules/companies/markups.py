from typing import Callable
from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from modules.companies.enums import CompanyCallback
from modules.companies.schemas import Company
from modules.users.schemas import User


def get_companies_list_markup(
    companies: List[Company],
    callback_type: Callable[[int], str] = CompanyCallback.detail,
) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for company in companies:
        markup.add(
            InlineKeyboardButton(
                text=company.name,
                callback_data=callback_type(company.id),
            ),
        )

    markup.add(
        InlineKeyboardButton(
            text='🏢 Создать компанию',
            callback_data=CompanyCallback.CREATE,
        ),
    )
    return markup


async def get_participants_list_markup(
    company_id: int,
    participants: List[User],
) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for participant in participants:
        markup.add(
            InlineKeyboardButton(
                text=f'@{participant.username}'
                if participant.username
                else f'{participant.first_name} {participant.last_name}',
                callback_data='none',
            ),
            InlineKeyboardButton(
                text='❌',
                callback_data=CompanyCallback.remove_participant(company_id, participant.chat_id),
            ),
        )
    return markup


def get_company_leave_markup(company_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            text='👋 Покинуть компанию',
            callback_data=CompanyCallback.leave(company_id),
        ),
    )
    return markup
