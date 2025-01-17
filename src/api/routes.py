from http import HTTPStatus

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.params import (
    DynamicPath,
    CodePath,
    OperationPath,
    ExchangeRetrieveQuery,
    ExchangeUploadForm,
    TempFile,
)
from src.core.config import LIMITER, LIMIT, LOG
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


@router.get(
    "/{dynamic}/retrieve",
    status_code=HTTPStatus.OK,
    tags=["API"],
    summary="Retrieves a code directory file",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_retrieve_file(
    request: Request, dynamic: DynamicPath, query: ExchangeRetrieveQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value, "query": query.model_dump()})
    return await UseCases.retrieve_file(request, dynamic, query)


@router.post(
    "/{dynamic}/upload",
    status_code=HTTPStatus.OK,
    tags=["API"],
    summary="Uploads a code directory file",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_upload_file(
    request: Request, dynamic: DynamicPath, form: ExchangeUploadForm
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value, "form": form.model_dump()})
    return await UseCases.upload_file(request, dynamic, form)


@router.put(
    "/{dynamic}/exchange",
    status_code=HTTPStatus.OK,
    tags=["API"],
    summary="Exchange files of a dynamic code directory",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_exchange(
    request: Request, dynamic: DynamicPath, form: ExchangeUploadForm
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value, "form": form.model_dump()})
    return await UseCases.file_exchange(request, dynamic, form)


@router.get(
    "/{dynamic}/list",
    status_code=HTTPStatus.OK,
    tags=["Code Directory"],
    summary="List a dynamic code directories",
    response_model=SuccessResponse,
)
async def api_list(request: Request, dynamic: DynamicPath) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value})
    return await UseCases.list_code_directories(request, dynamic)


@router.post(
    "/{dynamic}/add",
    status_code=HTTPStatus.OK,
    tags=["Code Directory"],
    summary="Add a dynamic new code directory",
    response_model=SuccessResponse,
)
async def api_add(request: Request, dynamic: DynamicPath) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value})
    return await UseCases.add_code_directory(request, dynamic)


@router.delete(
    "/{dynamic}/remove/{code}",
    status_code=HTTPStatus.OK,
    tags=["Code Directory"],
    summary="Remove a dynamic code directory",
    response_model=SuccessResponse,
)
async def api_remove(
    request: Request, dynamic: DynamicPath, code: CodePath
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
async def api_download(
    dynamic: DynamicPath, temp_file: TempFile
) -> FileResponse:
    LOG.debug({"dynamic": dynamic.value})
    return await UseCases.download_directory_tree(dynamic, temp_file)


@router.get(
    "/{dynamic}/dynamic-report",
    status_code=HTTPStatus.OK,
    tags=["Report"],
    summary="Retrieve a dynamic reports",
    response_model=SuccessResponse,
)
async def api_dynamic_report(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value})
    return await Repository.get_dynamic_reports(request, dynamic)


@router.get(
    "/{dynamic}/file-report",
    status_code=HTTPStatus.OK,
    tags=["Report"],
    summary="Retrieve a file report",
    response_model=SuccessResponse,
)
async def api_file_report(
    request: Request, dynamic: DynamicPath, query: ExchangeRetrieveQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value, "query": query.model_dump()})
    return await Repository.get_file_report(request, dynamic, query)


@router.get(
    "/{dynamic}/operation-report/{operation}",
    status_code=HTTPStatus.OK,
    tags=["Report"],
    summary="Retrieve a operation reports",
    response_model=SuccessResponse,
)
async def api_operation_report(
    request: Request, dynamic: DynamicPath, operation: OperationPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic.value, "operation": operation.name})
    return await Repository.get_operation_reports(request, dynamic, operation)
