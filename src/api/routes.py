from http import HTTPStatus

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.enums import Dynamic
from src.common.types import CodeQuery, ExchangeForm, TempFile
from src.core.config import LIMITER, LOG
from src.core.repository import Repository
from src.core.use_cases import UseCases

router = APIRouter(prefix="/v1/ifms-dev-competition/api")


@router.post(
    "/create",
    status_code=HTTPStatus.OK,
    tags=["Directory Tree"],
    summary="Generates the entire directory tree",
    response_model=SuccessResponse,
)
async def api_create(request: Request) -> SuccessJSON:
    return await UseCases.create_directory_tree(request)


@router.put(
    "/{dynamic}/exchange",
    status_code=HTTPStatus.OK,
    tags=["API"],
    summary="Exchange files of a dynamic code directory",
    response_model=SuccessResponse,
)
@LIMITER.limit("30/5seconds")
async def api_exchange(
    request: Request, dynamic: Dynamic, form: ExchangeForm
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value, "form": form.model_dump()})
    return await UseCases.file_exchange(request, dynamic, form)


@router.get(
    "/{dynamic}/list",
    status_code=HTTPStatus.OK,
    tags=["API"],
    summary="List a dynamic code directories",
    response_model=SuccessResponse,
)
async def api_list(request: Request, dynamic: Dynamic) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value})
    return await UseCases.list_code_directories(request, dynamic)


@router.post(
    "/{dynamic}/add",
    status_code=HTTPStatus.OK,
    tags=["API"],
    summary="Add a dynamic new code directory",
    response_model=SuccessResponse,
)
async def api_add(request: Request, dynamic: Dynamic) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value})
    return await UseCases.add_code_directory(request, dynamic)


@router.delete(
    "/{dynamic}/remove",
    status_code=HTTPStatus.OK,
    tags=["API"],
    summary="Remove a dynamic code directory",
    response_model=SuccessResponse,
)
async def api_remove(
    request: Request, dynamic: Dynamic, code: CodeQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value, "code": code})
    return await UseCases.remove_code_directory(request, dynamic, code)


@router.get(
    "/{dynamic}/download",
    status_code=HTTPStatus.OK,
    tags=["Download"],
    summary="Downloads a dynamic directory tree",
    response_class=FileResponse,
)
async def api_download(dynamic: Dynamic, temp_file: TempFile) -> FileResponse:
    LOG.debug({"dynamic": dynamic.value})
    return await UseCases.download_directory_tree(dynamic, temp_file)


@router.get(
    "/{dynamic}/report",
    status_code=HTTPStatus.OK,
    tags=["Report"],
    summary="Retrieve a dynamic exchange reports",
    response_model=SuccessResponse,
)
async def api_report(request: Request, dynamic: Dynamic) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value})
    return await Repository.get_dynamic_reports(request, dynamic)
