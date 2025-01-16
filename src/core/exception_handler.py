from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from pydantic_core import ValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.presenters import ErrorJSON
from src.core.config import LOG


class ExceptionHandler:
    """Handles exceptions and returns their JSON representation"""

    __PYDANTIC_ERROR = "Pydantic validation error: {} validation errors for {}"
    __RESPONSE_ERROR = "Validation error in response <{}>"
    __REQUEST_ERROR = "Validation error in request <{}>"
    __RATE_LIMIT_ERROR = "Request rate limit of {} exceeded"

    @property
    def handlers(self) -> dict:
        return {
            StarletteHTTPException: self.starlette_http_exception,
            HTTPException: self.fastapi_http_exception,
            RequestValidationError: self.request_validation_error,
            ResponseValidationError: self.response_validation_error,
            ValidationError: self.pydantic_validation_error,
            RateLimitExceeded: self.rate_limit_error,
        }

    async def starlette_http_exception(
        self, request: Request, exc: StarletteHTTPException
    ) -> ErrorJSON:
        LOG.error(exc.detail)
        return ErrorJSON(request, exc.status_code, str(exc.detail))

    async def fastapi_http_exception(
        self, request: Request, exc: HTTPException
    ) -> ErrorJSON:
        LOG.error(exc.detail)
        return ErrorJSON(request, exc.status_code, str(exc.detail))

    async def request_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> ErrorJSON:
        first_error: dict = exc.errors()[0]
        message = self.__REQUEST_ERROR.format(first_error.get("msg", "null"))

        LOG.error(message)
        LOG.exception(exc)

        return ErrorJSON(
            request,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            message,
            exc.errors(),
        )

    async def response_validation_error(
        self, request: Request, exc: ResponseValidationError
    ) -> ErrorJSON:
        first_error: dict = exc.errors()[0]
        message = self.__RESPONSE_ERROR.format(first_error.get("msg", "null"))

        LOG.error(message)
        LOG.exception(exc)

        return ErrorJSON(
            request,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            message,
            exc.errors(),
        )

    async def pydantic_validation_error(
        self, request: Request, exc: ValidationError
    ) -> ErrorJSON:
        message = self.__PYDANTIC_ERROR.format(exc.error_count(), exc.title)

        LOG.error(message)
        LOG.exception(exc)

        return ErrorJSON(
            request,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            message,
            exc.errors(),
        )

    async def rate_limit_error(
        self, request: Request, exc: RateLimitExceeded
    ) -> ErrorJSON:
        message = self.__RATE_LIMIT_ERROR.format(exc.detail)
        LOG.error(message)
        return ErrorJSON(request, HTTPStatus.TOO_MANY_REQUESTS, message)
