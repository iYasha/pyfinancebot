import string
from collections import defaultdict
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
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
    ) -> Operation:
        values = operation_create.dict()
        values['created_at'] = datetime.now()
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
                repeat_days=repeat_time['days'] if repeat_time is not None else None,
                is_regular_operation=repeat_time is not None,
            ),
            categories,
        )

    @classmethod
    async def approve_operation(
        cls: Type['OperationService'],
        operation_id: int,
        category: str,
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
        is_approved: bool = True,
        is_regular_operation: bool = True,
        has_full_amount: Optional[bool] = None,
    ) -> List[Operation]:
        operations = await cls.repository.get_regular_operations(
            is_approved=is_approved,
            is_regular_operation=is_regular_operation,
            has_full_amount=has_full_amount,
        )
        return [Operation(**operation) for operation in operations]

    @classmethod
    async def get_stats(
        cls: Type['OperationService'],
        date_from: datetime,
        date_to: datetime,
    ) -> Dict[str, float]:
        return await cls.repository.get_stats(date_from=date_from, date_to=date_to)

    @classmethod
    async def get_operations(
        cls: Type['OperationService'],
        page: int = 1,
    ) -> PaginatedSchema[List[Operation]]:
        operations = await cls.repository.get_operations(page=page)

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