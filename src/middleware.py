from http import HTTPStatus
from json import dumps
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from pydantic_core import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response

from src.config import LOG
from src.exceptions import ExceptionJSON


class TracingTimeExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware tracing, process time and exceptions"""

    __PROCESS_TIME = "X-Process-Time"
    __REQUEST_ERROR = "Validation error in request <{}>"
    __RESPONSE_ERROR = "Validation error in response <{}>"
    __PYDANTIC_ERROR = "Pydantic validation error: {} validation errors for {}"
    __UNEXPECTED_ERROR = "Unexpected error <{}>"

    def __init__(self, app: FastAPI):
        """Middleware tracing, process time and exceptions"""
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response | ExceptionJSON:
        start_time = perf_counter()

        try:
            response = await call_next(request)

        except HTTPException as exc:
            if not exc.detail.isalnum():
                exc.detail = dumps(exc.detail)
            LOG.error(exc.detail)
            response = ExceptionJSON(request, exc.status_code, exc.detail)

        except StarletteHTTPException as exc:
            LOG.error(exc.detail)
            response = ExceptionJSON(request, exc.status_code, exc.detail)

        except RequestValidationError as exc:
            first_error: dict = exc.errors()[0]
            message = self.__REQUEST_ERROR.format(
                first_error.get("msg", "null")
            )

            LOG.error(message)
            LOG.exception(exc)

            response = ExceptionJSON(
                request,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                message,
                exc.errors(),
            )

        except ResponseValidationError as exc:
            first_error: dict = exc.errors()[0]
            message = self.__RESPONSE_ERROR.format(
                first_error.get("msg", "null")
            )

            LOG.error(message)
            LOG.exception(exc)

            response = ExceptionJSON(
                request,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                message,
                exc.errors(),
            )

        except ValidationError as exc:
            message = self.__PYDANTIC_ERROR.format(
                exc.error_count(), exc.title
            )

            LOG.error(message)
            LOG.exception(exc)

            response = ExceptionJSON(
                request,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                message,
                exc.errors(),
            )

        except Exception as exc:  # pylint: disable=W0718
            message = exc.args[0] if exc.args[0] else self.__UNEXPECTED_ERROR

            LOG.error(message)
            LOG.exception(exc)

            response = ExceptionJSON(
                request,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                self.__UNEXPECTED_ERROR.format(repr(exc)),
            )

        process_time = perf_counter() - start_time
        response.headers[self.__PROCESS_TIME] = f"{process_time:.2f}s"

        return response
