import uvicorn
from fastapi import FastAPI

from config import Environment, settings
from webserver.api.monobank.views import router as monobank_router
from webserver.sentry import init_sentry

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None if settings.ENVIRONMENT == Environment.PROD else '/docs',
    redoc_url=None if settings.ENVIRONMENT == Environment.PROD else '/redoc',
    openapi_url=None if settings.ENVIRONMENT == Environment.PROD else '/openapi.json',
)

if settings.SENTRY_DSN:
    app = init_sentry(app)

app.include_router(monobank_router)


def run() -> None:
    uvicorn.run('webserver.app:app', host='0.0.0.0', port=8888, access_log=False, reload=True)


if __name__ == '__main__':
    run()
