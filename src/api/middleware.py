from http import HTTPStatus
from time import perf_counter

from fastapi import FastAPI, Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response

from src.api.presenters import ErrorJSON
from src.core.config import LOG
from src.utils.formater import format_error, get_error_message


class TracingTimeExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware tracing, process time and uncaught exceptions"""

    __PROCESS_TIME = "X-Process-Time"

    def __init__(self, app: FastAPI):
        """Middleware tracing, process time and uncaught exceptions"""
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response | ErrorJSON:
        start_time = perf_counter()

        try:
            response = await call_next(request)

        except Exception as exc:  # pylint: disable=W0718
            message = get_error_message(exc)

            LOG.error(message)
            LOG.exception(exc)

            response = ErrorJSON(
                request,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                format_error(exc, message),
            )

        process_time = perf_counter() - start_time
        response.headers[self.__PROCESS_TIME] = f"{process_time:.2f}s"

        LOG.trace(request, response.status_code, process_time)

        return response
