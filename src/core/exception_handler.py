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
from src.core.config import LOG, ERROR_MESSAGE
from src.utils.formater import format_error


class ExceptionHandler:
    """Handles exceptions and returns their JSON representation"""

    @property
    def handlers(self) -> dict:
        return {
            StarletteHTTPException: self.starlette_http_exception,
            HTTPException: self.starlette_http_exception,
            RequestValidationError: self.request_validation_error,
            ResponseValidationError: self.validation_error,
            ValidationError: self.validation_error,
            RateLimitExceeded: self.rate_limit_error,
        }

    async def starlette_http_exception(
        self, request: Request, exc: StarletteHTTPException | HTTPException
    ) -> ErrorJSON:
        LOG.error(exc.detail)
        return ErrorJSON(
            request, exc.status_code, format_error(exc, exc.detail)
        )

    async def request_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> ErrorJSON:
        first_error: dict = exc.errors()[0]
        message = first_error.get("msg", ERROR_MESSAGE)

        LOG.error(message)
        LOG.exception(exc)

        return ErrorJSON(
            request,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            format_error(exc, message),
            exc.errors(),
        )

    async def validation_error(
        self, request: Request, exc: ResponseValidationError | ValidationError
    ) -> ErrorJSON:
        first_error: dict = exc.errors()[0]
        message = first_error.get("msg", ERROR_MESSAGE)

        LOG.error(message)
        LOG.exception(exc)

        return ErrorJSON(
            request,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            format_error(exc, message),
            exc.errors(),
        )

    async def rate_limit_error(
        self, request: Request, exc: RateLimitExceeded
    ) -> ErrorJSON:
        message = f"Request rate limit of {exc.detail} exceeded"
        LOG.error(message)
        return ErrorJSON(
            request,
            HTTPStatus.TOO_MANY_REQUESTS,
            format_error(exc, message),
        )
