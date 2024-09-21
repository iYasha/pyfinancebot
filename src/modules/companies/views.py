from typing import Union

import aiogram.utils.markdown as md
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, ParseMode
from aiogram.utils.text_decorations import markdown_decoration
from databases.core import Transaction

from config import bot, dp, settings
from modules.companies.enums import CompanyCallback
from modules.companies.markups import get_companies_list_markup, get_company_leave_markup, get_participants_list_markup
from modules.companies.schemas import CompanyCreateState
from modules.companies.services import CompanyService
from modules.helps.enums import Command
from sdk import utils
from sdk.decorators import error_handler_decorator, transaction_decorator


@dp.message_handler(commands=[Command.COMPANIES])
@dp.callback_query_handler(
    lambda c: c.data and c.data == Command.COMPANIES,
)
@error_handler_decorator
async def get_companies(data: Union[types.Message, types.CallbackQuery]) -> None:
    if isinstance(data, types.CallbackQuery):
        message = data.message
    else:
        message = data
    companies = await CompanyService.get_my_companies(message.chat.id)
    markup = get_companies_list_markup(companies, message.chat.id)
    if isinstance(data, types.CallbackQuery):
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text='Ваши компании:',
            reply_markup=markup,
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text='Ваши компании:',
            reply_markup=markup,
        )


@dp.message_handler(commands=[Command.CHOOSE_COMPANY])
@error_handler_decorator
async def choose_company(message: types.Message) -> None:
    companies = await CompanyService.get_my_companies(message.chat.id)
    chat_id = message.chat.id
    markup = get_companies_list_markup(companies, chat_id, callback_type=CompanyCallback.select)
    await bot.send_message(
        chat_id=message.chat.id,
        text='Выбор активной компании:',
        reply_markup=markup,
    )


@dp.callback_query_handler(lambda callback: callback.data.startswith(CompanyCallback.CREATE))
@error_handler_decorator
async def create_company(callback: types.CallbackQuery) -> None:
    await CompanyCreateState.name.set()
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text='Отправьте следующим сообщением название компании',
        reply_markup=utils.get_cancel_markup(),
    )


@dp.message_handler(lambda message: message.text.lower() == '❌ отмена', state='*')
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await bot.send_message(
            chat_id=message.chat.id,
            text='Операция отменена!',
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return
    await state.finish()
    await bot.send_message(
        chat_id=message.chat.id,
        text='Компания не создана!',
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await message.delete()


@dp.message_handler(state=CompanyCreateState.name)
@error_handler_decorator
@transaction_decorator
async def finish_company_create(message: types.Message, state: FSMContext, *, transaction: Transaction) -> None:
    await state.finish()
    company_name = message.text.strip()
    company_id = await CompanyService.create_company(
        name=company_name,
        creator_id=message.chat.id,
    )
    await CompanyService.add_participant(
        company_id=company_id,
        chat_id=message.chat.id,
    )
    await transaction.commit()
    bot_info = await bot.me
    await bot.send_message(
        chat_id=message.chat.id,
        text=md.text(
            md.text(f'✅ Компания "<b>{company_name}</b>" успешно создана!'),
            md.text(
                '🤝 Чтобы добавить участников в компанию, отправьте им ссылку:',
                '<code>https://t.me/{}?start={}_{}</code>'.format(
                    bot_info.username,
                    company_id,
                    message.chat.id,
                ),
            ),
            sep='\n',
        ),
        parse_mode=settings.PARSE_MODE,
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.callback_query_handler(lambda callback: callback.data.startswith(CompanyCallback.DETAIL))
@error_handler_decorator
async def get_company_detail(callback: types.CallbackQuery) -> None:
    company_id = int(
        callback.data.replace(f'{CompanyCallback.DETAIL}_', '').split(
            '_',
        )[0],
    )
    company = await CompanyService.company_detail(company_id)
    participant_count = len(company.participants)
    text = [
        md.text(f'🏢 Компания: *{company.name}*'),
        md.text(
            'Участники:',
            *[
                md.text(
                    ('└' if idx + 1 == participant_count else '├')
                    + '  '
                    + markdown_decoration.link(
                        f'@{participant.username}'
                        if participant.username
                        else f'{participant.first_name} {participant.last_name}',
                        f'tg://user?id={participant.chat_id}',
                    ),
                    ' (создатель)' if participant.chat_id == company.creator_id else '',
                    sep='',
                )
                for idx, participant in enumerate(company.participants)
            ],
            sep='\n',
        ),
    ]
    if company.creator_id == callback.message.chat.id:
        bot_info = await bot.me
        text.append(
            md.text(
                '🤝 Чтобы добавить участников в компанию, отправьте им ссылку:',
                '`https://t.me/{}?start={}_{}`'.format(
                    bot_info.username,
                    company_id,
                    company.creator_id,
                ),
            ),
        )
        reply_markup = await get_participants_list_markup(company_id, company.participants)
        reply_markup.add(
            InlineKeyboardButton(
                '🗑 Удалить компанию',
                callback_data=CompanyCallback.delete(company_id),
            ),
        )
    else:
        reply_markup = get_company_leave_markup(company_id)
    reply_markup.add(
        InlineKeyboardButton(
            '🔙 Назад',
            callback_data=Command.COMPANIES,
        ),
    )

    await bot.edit_message_text(
        text=md.text(
            *text,
            sep='\n',
        ),
        chat_id=callback.message.chat.id,
        parse_mode=ParseMode.MARKDOWN,
        message_id=callback.message.message_id,
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(lambda callback: callback.data.startswith(CompanyCallback.SELECT))
@error_handler_decorator
async def select_company(callback: types.CallbackQuery) -> None:
    company_id = int(
        callback.data.replace(
            f'{CompanyCallback.SELECT}_',
            '',
        ),
    )
    await CompanyService.get_company(company_id)
    settings.SELECTED_COMPANIES[callback.message.chat.id] = company_id
    companies = await CompanyService.get_my_companies(callback.message.chat.id)
    chat_id = callback.message.chat.id
    markup = get_companies_list_markup(companies, chat_id, callback_type=CompanyCallback.select)
    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=callback.message.message_id,
        reply_markup=markup,
    )


@dp.callback_query_handler(lambda callback: callback.data.startswith(CompanyCallback.DELETE))
@error_handler_decorator
async def delete_company(callback: types.CallbackQuery) -> None:
    company_id = int(
        callback.data.replace(
            f'{CompanyCallback.DELETE}_',
            '',
        ),
    )
    company = await CompanyService.get_company(company_id)
    if company.creator_id != callback.message.chat.id:
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text='❌ Вы не являетесь создателем компании!',
        )
        return
    await CompanyService.delete_company(company_id)
    await bot.answer_callback_query(
        callback_query_id=callback.id,
        text=f'✅ Компания "{company.name}" удалена!',
    )
    callback.data = Command.COMPANIES
    await get_companies(callback)


@dp.callback_query_handler(lambda callback: callback.data.startswith(CompanyCallback.LEAVE))
@error_handler_decorator
async def leave_company(callback: types.CallbackQuery) -> None:
    company_id = int(
        callback.data.replace(
            f'{CompanyCallback.LEAVE}_',
            '',
        ),
    )
    company = await CompanyService.get_company(company_id)
    if company.creator_id == callback.message.chat.id:
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text='❌ Вы не можете покинуть свою компанию!',
        )
        return
    await CompanyService.remove_participant(
        company_id=company_id,
        chat_id=callback.message.chat.id,
    )
    await bot.answer_callback_query(
        callback_query_id=callback.id,
        text='✅ Вы покинули компанию!',
    )
    callback.data = Command.COMPANIES
    await get_companies(callback)


@dp.callback_query_handler(
    lambda callback: callback.data.startswith(CompanyCallback.REMOVE_PARTICIPANT),
)
@error_handler_decorator
async def remove_participant(callback: types.CallbackQuery) -> None:
    company_id, participant_chat_id = callback.data.replace(
        f'{CompanyCallback.REMOVE_PARTICIPANT}_',
        '',
    ).split('_')
    company_id = int(company_id)
    participant_chat_id = int(participant_chat_id)
    company = await CompanyService.get_company(company_id)
    if company.creator_id != callback.message.chat.id:
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text='❌ Вы не являетесь создателем компании!',
        )
        return
    if company.creator_id == participant_chat_id:
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text='❌ Вы не можете удалить создателя компании!',
        )
        return
    await CompanyService.remove_participant(
        company_id=company_id,
        chat_id=participant_chat_id,
    )
    await bot.answer_callback_query(
        callback_query_id=callback.id,
        text='✅ Участник удален!',
    )
    await bot.send_message(
        chat_id=participant_chat_id,
        text=f'😢 Вас удалили из компании "<b>{company.name}</b>"!',
        parse_mode=settings.PARSE_MODE,
    )
    callback.data = CompanyCallback.detail(company_id)
    await get_company_detail(callback)
