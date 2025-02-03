from http import HTTPStatus

from fastapi import Request
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.types import DynamicPath, OperationPath, RetrieveFileQuery
from src.core.config import LIMIT, LIMITER, LOG, ROUTE_PREFIX
from src.use_cases.reports import (
    dynamic_reports,
    file_report,
    operation_reports,
)

router = APIRouter(prefix=ROUTE_PREFIX, tags=["Reports"])


@router.get(
    "/{dynamic}/dynamic-report",
    status_code=HTTPStatus.OK,
    summary="Retrieve a dynamic reports",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_dynamic_reports(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await dynamic_reports(request, dynamic)


@router.get(
    "/{dynamic}/file-report",
    status_code=HTTPStatus.OK,
    summary="Retrieve a file report",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_file_report(
    request: Request, dynamic: DynamicPath, query: RetrieveFileQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "query": query.model_dump()})
    return await file_report(request, dynamic, query)


@router.get(
    "/{dynamic}/operation-report/{operation}",
    status_code=HTTPStatus.OK,
    summary="Retrieve a operation reports",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_operation_reports(
    request: Request, dynamic: DynamicPath, operation: OperationPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "operation": operation.value})
    return await operation_reports(request, dynamic, operation)
