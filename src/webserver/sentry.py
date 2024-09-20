from typing import Callable

import sentry_sdk
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config import settings


class SentryMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self: 'SentryMiddleware',
        request: Request,
        call_next: Callable,
    ) -> Response:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag('app', 'backend')
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag('error_type', type(e))
            raise e


def init_sentry(app: FastAPI) -> FastAPI:
    sentry_sdk.init(  # type: ignore
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[],
        traces_sample_rate=1.0,
    )

    app.add_middleware(SentryMiddleware)

    return app
