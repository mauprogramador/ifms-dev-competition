from http import HTTPStatus

from fastapi import Request
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.types import CodePath, DynamicPath
from src.core.config import LOG, ROUTE_PREFIX
from src.use_cases.code_dirs import (
    add_code_dir,
    list_code_dirs,
    remove_code_dir,
)

router = APIRouter(prefix=ROUTE_PREFIX, tags=["Code Dirs"])


# "/{dynamic}/list-code-dirs",
@router.get(
    "/{dynamic}/list",
    status_code=HTTPStatus.OK,
    summary="List a dynamic code dirs",
    response_model=SuccessResponse,
)
async def api_list_code_dirs(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await list_code_dirs(request, dynamic)


# "/{dynamic}/add-code-dir",
@router.post(
    "/{dynamic}/add",
    status_code=HTTPStatus.OK,
    summary="Add a dynamic new code dir",
    response_model=SuccessResponse,
)
async def api_add_code_dir(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await add_code_dir(request, dynamic)


# "/{dynamic}/remove-code-dir/{code}",
@router.delete(
    "/{dynamic}/remove/{code}",
    status_code=HTTPStatus.OK,
    summary="Remove a dynamic code dir",
    response_model=SuccessResponse,
)
async def api_remove_code_dir(
    request: Request, dynamic: DynamicPath, code: CodePath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "code": code})
    return await remove_code_dir(request, dynamic, code)
