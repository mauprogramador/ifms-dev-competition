from datetime import datetime
from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from pydantic_core import PydanticUndefined


class BaseResponse(BaseModel):
    """Base class for JSON responses"""

    success: bool
    code: int
    status: str
    message: str
    timestamp: str = datetime.now().isoformat()
    request: dict[str, Any]

    @field_validator("request", mode="before")
    @classmethod
    def get_request_data(cls, request: Request) -> dict[str, Any]:
        return {
            "host": request.client.host if request.client else "127.0.0.1",
            "port": request.client.port if request.client else 8000,
            "method": request.method,
            "url": request.url.path,
        }


class SuccessResponse(BaseResponse):
    """JSON success response"""

    data: dict[str, Any] | None = None


class ErrorResponse(BaseResponse):
    """JSON error response"""

    errors: list[dict[str, Any]] | None = None


class SuccessJSON(JSONResponse):
    """Success JSON representation response"""

    def __init__(
        self,
        request: Request,
        message: str,
        data: dict[str, Any] | None = None,
        code: HTTPStatus = None,
    ) -> None:
        """Success JSON representation response"""
        if code is None:
            code = HTTPStatus.OK

        content = SuccessResponse(
            success=True,
            code=code,
            status=HTTPStatus(code).phrase,
            message=message,
            request=request,
            data=data,
        )

        super().__init__(content.model_dump(), code)


class ErrorJSON(JSONResponse):
    """Error JSON representation response"""

    __KEY = "input"

    def __init__(
        self,
        request: Request,
        code: int,
        message: str,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        """Error JSON representation response"""
        if errors is not None:
            errors = list(map(self.__filter, errors))

        content = ErrorResponse(
            success=False,
            code=code,
            status=HTTPStatus(code).phrase,
            message=message,
            request=request,
            errors=errors,
        )
        super().__init__(content.model_dump(), code)

    def __filter(self, item: dict[str, Any]) -> dict[str, Any]:
        if self.__KEY in item and item[self.__KEY] is PydanticUndefined:
            item[self.__KEY] = "PydanticUndefined"
        return item
