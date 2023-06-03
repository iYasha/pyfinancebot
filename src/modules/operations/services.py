import string
from calendar import monthrange
from collections import defaultdict
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import Union

from config import category_model
from config import nlp
from config import operation_model
from modules.operations.enums import CurrencyEnum
from modules.operations.enums import ExpenseCategoryEnum
from modules.operations.enums import OperationType
from modules.operations.enums import RepeatType
from modules.operations.repositories import OperationRepository
from modules.operations.schemas import Operation
from modules.operations.schemas import OperationCreate
from modules.operations.schemas import OperationImport
from modules.operations.schemas import OperationUpdate
from spacy.lang.ru import STOP_WORDS

from sdk.repositories import WhereModifier
from sdk.schemas import PaginatedSchema


class OperationService:
    repository = OperationRepository

    @classmethod
    async def create_operation(
        cls: Type['OperationService'],
        operation_create: OperationCreate,
        company_id: int,
    ) -> Operation:
        values = operation_create.dict()
        values['created_at'] = datetime.now()
        values['company_id'] = company_id
        operation_id = await cls.repository.create(**values)
        return Operation(
            id=operation_id,
            **values,
        )

    @classmethod
    def preprocess_text(cls: Type['OperationService'], text: str) -> str:
        text = text.lower()

        tokens = [token.lemma_.strip() for token in nlp(text)]

        return ' '.join(
            [
                t
                for t in tokens
                if t not in STOP_WORDS and t not in string.punctuation and not t.isdigit()
            ],
        )

    @classmethod
    def get_operation_entities(
        cls: Type['OperationService'],
        text: str,
    ) -> Dict[str, Union[str, List[str], List[tuple]]]:
        text = text.replace('- ', '-') if text.startswith('- ') else text
        doc = operation_model(text)
        single_entities = ('AMOUNT', 'CURRENCY', 'FOR', 'EVERYDAY', 'EVERYWEEK', 'EVERYMONTH')
        multiple_entities = ('NUMBEROFDAY',)
        weekdays = {
            'MONDAY': 0,
            'TUESDAY': 1,
            'WEDNESDAY': 2,
            'THURSDAY': 3,
            'FRIDAY': 4,
            'SATURDAY': 5,
            'SUNDAY': 6,
        }
        weekdays_values = list(weekdays.keys())
        entities = defaultdict(list)
        for entity in doc.ents:
            if entity.label_ in single_entities:
                entities[entity.label_] = entity.text
            elif entity.label_ in multiple_entities:
                entities[entity.label_].append(entity.text)
            elif entity.label_ in weekdays_values:
                entities['WEEKDAYS'].append(weekdays[entity.label_])
            elif entity.label_ == 'LASTDAY':
                entities['WEEKDAYS'].append('last')
        return entities

    @classmethod
    def get_categories(cls: Type['OperationService'], text: str) -> List[ExpenseCategoryEnum]:
        doc = category_model(cls.preprocess_text(text))
        categories = doc.cats
        return [
            ExpenseCategoryEnum(x.lower())
            for x in sorted(categories, key=categories.get, reverse=True)[:2]
        ]

    @classmethod
    def get_operation_regularity(
        cls: Type['OperationService'],
        entities: Dict[str, Union[str, List[str], List[tuple]]],
    ) -> Optional[Dict[str, Union[str, list]]]:
        if entities.get('EVERYDAY', False):
            return {'type': 'every_day', 'days': []}
        elif entities.get('EVERYWEEK', False):
            return {'type': 'every_week', 'days': entities.get('WEEKDAYS')}
        elif entities.get('EVERYMONTH', False):
            return {'type': 'every_month', 'days': entities.get('NUMBEROFDAY')}
        return None

    @classmethod
    def parse_operation(
        cls: Type['OperationService'],
        text: str,
        creator_id: int,
    ) -> Optional[Tuple[OperationCreate, List[ExpenseCategoryEnum]]]:
        entities = cls.get_operation_entities(text)
        description = entities.get('FOR')
        amount = int(entities.get('AMOUNT'))
        currency = entities.get('CURRENCY')
        operation_type = OperationType.get_operation_type(amount)
        repeat_time = cls.get_operation_regularity(entities)
        repeat_days = None
        if repeat_time is not None:
            repeat_days = repeat_time['days']
        categories = (
            cls.get_categories(description) if operation_type == OperationType.EXPENSE else []
        )
        return (
            OperationCreate(
                creator_id=creator_id,
                amount=abs(int(amount)),
                currency=CurrencyEnum.get(currency),
                operation_type=operation_type,
                description=description,
                repeat_type=repeat_time['type']
                if repeat_time is not None
                else RepeatType.NO_REPEAT,
                repeat_days=repeat_days,
                is_regular_operation=repeat_time is not None,
            ),
            categories,
        )

    @classmethod
    async def approve_operation(
        cls: Type['OperationService'],
        operation_id: int,
        category: Optional[str] = None,
    ) -> None:
        await cls.repository.approve_operation(operation_id, category)

    @classmethod
    async def delete_operation(cls: Type['OperationService'], operation_id: int) -> None:
        await cls.repository.delete([WhereModifier(id=operation_id)])

    @classmethod
    async def get_operation(
        cls: Type['OperationService'],
        operation_id: int,
    ) -> Optional[Operation]:
        operation = await cls.repository.get([WhereModifier(id=operation_id)])
        if not operation:
            return None
        return Operation(**operation)

    @classmethod
    async def update_operation(
        cls: Type['OperationService'],
        operation_id: int,
        operation_data: OperationUpdate,
    ) -> None:
        await cls.repository.update(
            fields=operation_data.dict(exclude_unset=True),
            modifiers=[WhereModifier(id=operation_id)],
        )

    @classmethod
    async def get_regular_operations(
        cls: Type['OperationService'],
        company_id: Optional[int] = None,
    ) -> List[Operation]:
        operations = await cls.repository.get_regular_operations(company_id)
        return [Operation(**dict(operation)) for operation in operations]

    @classmethod
    def get_every_day_operations(
        cls,
        base_operation_data: Dict[str, any],
        now: datetime,
        days_range: Sequence[int],
    ) -> List[Operation]:
        return [
            Operation(
                **base_operation_data,
                created_at=datetime(
                    year=now.year,
                    month=now.month,
                    day=day,
                    hour=8,
                    minute=0,
                    second=0,
                ),
            )
            for day in days_range
        ]

    @classmethod
    def get_month_operations(
        cls,
        base_operation_data: Dict[str, any],
        now: datetime,
        repeat_days: List[int],
        last_day: int,
    ) -> List[Operation]:
        return [
            Operation(
                **base_operation_data,
                created_at=datetime(
                    year=now.year,
                    month=now.month,
                    day=(last_day if day == 'last' else int(day)),
                    hour=8,
                    minute=0,
                    second=0,
                ),
            )
            for day in repeat_days
            if now.day < (last_day if day == 'last' else int(day)) <= last_day
        ]

    @classmethod
    def get_every_week_operations(
        cls,
        base_operation_data: Dict[str, any],
        now: datetime,
        repeat_days: List[str],
        weekdays: Dict[int, List[int]],
    ) -> List[Operation]:
        return [
            Operation(
                **base_operation_data,
                created_at=datetime(
                    year=now.year,
                    month=now.month,
                    day=day,
                    hour=8,
                    minute=0,
                    second=0,
                ),
            )
            for weekday in repeat_days
            for day in weekdays[int(weekday)]
        ]

    @classmethod
    async def get_future_operations(cls, company_id: int) -> Tuple[OperationImport]:
        operations = await OperationService.get_regular_operations(company_id)
        future_operations = []
        now = datetime.now()
        last_day = monthrange(now.year, now.month)[1]
        days_range = tuple(range(now.day + 1, last_day + 1))
        weekdays = defaultdict(list)
        for day in days_range:
            weekdays[datetime(year=now.year, month=now.month, day=day).weekday()].append(day)

        for operation in operations:
            base_operation_data = operation.dict(exclude={'created_at', 'is_regular_operation'})
            base_operation_data['is_regular_operation'] = False
            if operation.repeat_type == RepeatType.EVERY_DAY:
                future_operations += cls.get_every_day_operations(
                    base_operation_data,
                    now,
                    days_range,
                )
            elif operation.repeat_type == RepeatType.EVERY_MONTH:
                future_operations += cls.get_month_operations(
                    base_operation_data,
                    now,
                    operation.repeat_days,
                    last_day,
                )
            elif operation.repeat_type == RepeatType.EVERY_WEEK:
                future_operations += cls.get_every_week_operations(
                    base_operation_data,
                    now,
                    operation.repeat_days,
                    weekdays,
                )

        return tuple(sorted(future_operations, key=lambda x: x.created_at))

    @classmethod
    async def get_stats(
        cls: Type['OperationService'],
        date_from: datetime,
        date_to: datetime,
        company_id: int,
    ) -> Dict[str, float]:
        return await cls.repository.get_stats(
            date_from=date_from,
            date_to=date_to,
            company_id=company_id,
        )

    @classmethod
    async def get_operations(
        cls: Type['OperationService'],
        company_id: int,
        page: int = 1,
        is_regular_operation: bool = False,
    ) -> PaginatedSchema[List[Operation]]:
        operations = await cls.repository.get_operations(
            page=page,
            is_regular_operation=is_regular_operation,
            company_id=company_id,
        )

        return PaginatedSchema(
            total_count=operations['total'],
            page_count=operations['page_count'],
            next=page + 1 if page < operations['page_count'] else None,
            previous=page - 1 if page > 1 else None,
            results=[Operation(**operation) for operation in operations['operations']],
        )

    @classmethod
    async def get_operation_count(cls: Type['OperationService']) -> int:
        return await cls.repository.count([WhereModifier(is_approved=True)])

    @classmethod
    async def create_many_operations(
        cls: Type['OperationService'],
        operations: List[OperationCreate],
    ) -> None:
        await cls.repository.create_many([operation.dict() for operation in operations])

    @classmethod
    async def create_regular_operation(  # noqa: CCR001 TODO: Cognitive complexity is too high (9 > 7). Need to refactor
        cls,
        operation: Operation,
        now: datetime,
        last_month_day: int,
        is_approved: bool = False,
    ) -> Optional[Operation]:
        if operation.repeat_type == RepeatType.NO_REPEAT:
            return None
        is_current_day = (
            now.day in [last_month_day if x == 'last' else int(x) for x in operation.repeat_days]
            if operation.repeat_days
            else False
        )
        is_month_repeat = operation.repeat_type == RepeatType.EVERY_MONTH and is_current_day
        is_week_repeat = (
            operation.repeat_type == RepeatType.EVERY_WEEK
            and now.weekday() in operation.repeat_days
            if operation.repeat_days
            else False
        )
        is_every_day_repeat = operation.repeat_type == RepeatType.EVERY_DAY
        if is_month_repeat or is_week_repeat or is_every_day_repeat:
            operation_create = OperationCreate(
                creator_id=operation.creator_id,
                amount=operation.amount,
                received_amount=operation.amount if is_approved else None,
                currency=operation.currency,
                operation_type=operation.operation_type,
                category=operation.category,
                description=operation.description,
                repeat_type=operation.repeat_type,
                repeat_days=operation.repeat_days,
                is_approved=is_approved,
                is_regular_operation=False,
            )
            return await OperationService.create_operation(
                operation_create,
                company_id=operation.company_id,
            )
        return None
