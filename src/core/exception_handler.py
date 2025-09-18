from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from pydantic_core import PydanticUndefined, ValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.presenters import ErrorJSON, HTTPError
from src.core.config import ERROR_MESSAGE, LOG
from src.utils.formaters import format_error


class ExceptionHandler:
    """Handles exceptions and returns their JSON representation"""

    @property
    def handlers(self) -> dict:
        return {
            HTTPError: self.custom_http_error,
            StarletteHTTPException: self.starlette_http_exception,
            HTTPException: self.starlette_http_exception,
            RequestValidationError: self.fastapi_validation_error,
            ResponseValidationError: self.fastapi_validation_error,
            ValidationError: self.pydantic_validation_error,
            RateLimitExceeded: self.rate_limit_error,
        }

    async def custom_http_error(
        self, request: Request, exc: HTTPError
    ) -> ErrorJSON:
        LOG.error(exc.detail)
        LOG.exception(exc)
        return ErrorJSON(
            request,
            exc.status_code,
            format_error(exc, exc.detail),
            exc.errors,
        )

    async def starlette_http_exception(
        self, request: Request, exc: StarletteHTTPException | HTTPException
    ) -> ErrorJSON:
        LOG.error(exc.detail)
        LOG.exception(exc)
        return ErrorJSON(
            request, exc.status_code, format_error(exc, exc.detail)
        )

    async def fastapi_validation_error(
        self,
        request: Request,
        exc: RequestValidationError | ResponseValidationError,
    ) -> ErrorJSON:
        errors = list(map(self.__exception_filter, exc.errors()))
        first_error: dict = errors[0]
        message = first_error.get("msg", ERROR_MESSAGE)

        LOG.error(message)
        LOG.exception(exc)

        return ErrorJSON(
            request,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            format_error(exc, message),
            errors,
        )

    async def pydantic_validation_error(
        self, request: Request, exc: ValidationError
    ) -> ErrorJSON:
        errors = list(map(self.__undefined_filter, exc.errors()))
        first_error: dict = errors[0]
        message = first_error.get("msg", ERROR_MESSAGE)

        LOG.error(message)
        LOG.exception(exc)

        return ErrorJSON(
            request,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            format_error(exc, message),
            errors,
        )

    async def rate_limit_error(
        self, request: Request, exc: RateLimitExceeded
    ) -> ErrorJSON:
        message = f"Request rate limit of {exc.detail} exceeded"
        LOG.error(message)
        LOG.exception(exc)
        return ErrorJSON(
            request,
            HTTPStatus.TOO_MANY_REQUESTS,
            format_error(exc, message),
        )

    def __undefined_filter(self, item: dict[str, Any]) -> dict[str, Any]:
        if "input" in item and item["input"] is PydanticUndefined:
            item["input"] = "PydanticUndefined"
        return item

    def __exception_filter(self, item: dict[str, Any]) -> dict[str, Any]:
        if "ctx" in item and "error" in item["ctx"]:
            if isinstance(item["ctx"]["error"], Exception):
                item["ctx"]["error"] = type(item["ctx"]["error"]).__name__
        return item
