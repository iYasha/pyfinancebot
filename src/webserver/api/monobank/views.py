from fastapi import APIRouter
from starlette.responses import JSONResponse

from database import database
from modules.integrations import MonobankIntegrationService, MonobankService
from modules.integrations.monobank.schemas import WebhookRequest

router = APIRouter(prefix='/monobank', tags=['monobank'])


@router.get('/webhook/{secret}/')
async def monobank_webhook(secret: str):
    integration = await MonobankIntegrationService.check_integration_by_secret(secret)
    if not integration:
        return JSONResponse(status_code=404, content={'detail': 'Not Found'})
    return JSONResponse(status_code=200, content={'detail': 'OK'})


@router.post('/webhook/{secret}/')
async def create_operation_via_monobank(secret: str, webhook_data: WebhookRequest):
    integration = await MonobankIntegrationService.check_integration_by_secret(secret)
    if not integration:
        return JSONResponse(status_code=404, content={'detail': 'Not Found'})
    account_id = webhook_data.data.account
    account = await MonobankIntegrationService.get_account(integration, account_id)
    if account is None:
        async with database.transaction():
            client_info = await MonobankService(integration.integration_key).get_client_info()
            await MonobankIntegrationService.set_accounts(integration.chat_id, integration.company_id, client_info)
            is_active_account = any([True for account in client_info.accounts if account.id == account_id])
    else:
        is_active_account = account.is_active

    if is_active_account:
        await MonobankIntegrationService.create_operation(
            integration=integration,
            webhook_data=webhook_data,
        )
    return JSONResponse(status_code=200, content={'detail': 'OK'})
