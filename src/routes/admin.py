from http import HTTPStatus

from fastapi import Request
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.types import AnswerKeyFile, DynamicPath, LockQuery, WeightQuery
from src.core.config import LOG, ROUTE_PREFIX
from src.use_cases.admin import (
    clean_files,
    clean_reports,
    lock_requests,
    save_answer_key,
    set_weight,
)

router = APIRouter(prefix=ROUTE_PREFIX, tags=["Admin"])


@router.put(
    "/{dynamic}/lock-requests",
    status_code=HTTPStatus.OK,
    summary="Lock/Unlock sending requests of a dynamic",
    response_model=SuccessResponse,
)
async def api_lock_requests(
    request: Request, dynamic: DynamicPath, lock_status: LockQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "lock_status": lock_status.value})
    return await lock_requests(request, dynamic, lock_status)


@router.put(
    "/{dynamic}/set-weight",
    status_code=HTTPStatus.OK,
    summary="Sets the weight of the score calculation",
    response_model=SuccessResponse,
)
async def api_set_weight(
    request: Request, dynamic: DynamicPath, weight: WeightQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "weight": weight})
    return await set_weight(request, dynamic, weight)


@router.post(
    "/{dynamic}/answer-key",
    status_code=HTTPStatus.OK,
    summary="Saves a dynamic answer key image",
    response_model=SuccessResponse,
)
async def api_save_answer_key(
    request: Request, dynamic: DynamicPath, file: AnswerKeyFile
) -> SuccessJSON:
    LOG.debug(
        {
            "dynamic": dynamic,
            "filename": file.filename,
            "content_type": file.content_type,
        }
    )
    return await save_answer_key(request, dynamic, file)


@router.delete(
    "/{dynamic}/clean-reports",
    status_code=HTTPStatus.OK,
    summary="Removes a dynamic reports records",
    response_model=SuccessResponse,
)
async def api_clean_reports(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await clean_reports(request, dynamic)


@router.delete(
    "/{dynamic}/clean-files",
    status_code=HTTPStatus.OK,
    summary="Empties all files of a dynamic",
    response_model=SuccessResponse,
)
async def api_clean_files(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await clean_files(request, dynamic)
