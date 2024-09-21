from fastapi import APIRouter
from starlette.responses import JSONResponse

from modules.integrations import MonobankIntegrationService
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
    # TODO: Track if account id is in db, if not, retrieve all accounts again and save them
    integration = await MonobankIntegrationService.check_integration_by_secret(secret)
    if not integration:
        return JSONResponse(status_code=404, content={'detail': 'Not Found'})
    if await MonobankIntegrationService.is_active_account(integration, webhook_data.data.account):
        await MonobankIntegrationService.create_operation(
            integration=integration,
            webhook_data=webhook_data,
        )
    return JSONResponse(status_code=200, content={'detail': 'OK'})
