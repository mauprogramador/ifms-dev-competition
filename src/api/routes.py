from http import HTTPStatus

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.enums import FileType, Operation
from src.common.params import (
    DynamicPath,
    HasLock,
    OperationPath,
    RetrieveFileQuery,
    TempFile,
    UploadFileForm,
)
from src.core.config import LIMIT, LIMITER, LOG
from src.core.use_cases import UseCases
from src.repository import ReportRepository

router = APIRouter(prefix="/v2/ifms-dev-competition/api")


# "/{dynamic}/retrieve-file",
@router.get(
    "/{dynamic}/retrieve",
    status_code=HTTPStatus.OK,
    tags=["Files"],
    dependencies=[HasLock],
    summary="Retrieves a code dir file",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def retrieve_file(
    request: Request,
    dynamic: DynamicPath,
    query: RetrieveFileQuery,
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "query": query.model_dump()})

    response = await UseCases.retrieve_file(request, dynamic, query)
    ReportRepository.add_report(dynamic, query, Operation.RETRIEVE)

    return response


# "/{dynamic}/upload-file",
@router.post(
    "/{dynamic}/upload",
    status_code=HTTPStatus.OK,
    tags=["Files"],
    dependencies=[HasLock],
    summary="Uploads a code dir file",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def upload_file(
    request: Request, dynamic: DynamicPath, form: UploadFileForm
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "form": form.model_dump()})

    response = await UseCases.upload_file(request, dynamic, form)
    similarity = None

    if form.type == FileType.CSS:
        try:
            similarity = await UseCases.compare_similarity(dynamic, form.code)
        except Exception as error:  # pylint: disable=W0718
            LOG.error("Failed to compare page to answer key")
            LOG.exception(error)

    ReportRepository.add_report(dynamic, form, Operation.UPLOAD, similarity)

    return response


@router.get(
    "/{dynamic}/download",
    status_code=HTTPStatus.OK,
    tags=["Download"],
    summary="Downloads a dynamic dir tree",
    response_class=FileResponse,
)
async def download_dir_tree(
    dynamic: DynamicPath, temp_file: TempFile
) -> FileResponse:
    LOG.debug({"dynamic": dynamic, "temp_file": temp_file.name})
    return await UseCases.download_dir_tree(dynamic, temp_file)


@router.get(
    "/{dynamic}/dynamic-report",
    status_code=HTTPStatus.OK,
    tags=["Reports"],
    summary="Retrieve a dynamic reports",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def dynamic_report(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await ReportRepository.get_dynamic_reports(request, dynamic)


@router.get(
    "/{dynamic}/file-report",
    status_code=HTTPStatus.OK,
    tags=["Reports"],
    summary="Retrieve a file report",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def file_report(
    request: Request, dynamic: DynamicPath, query: RetrieveFileQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "query": query.model_dump()})
    return await ReportRepository.get_file_report(request, dynamic, query)


@router.get(
    "/{dynamic}/operation-report/{operation}",
    status_code=HTTPStatus.OK,
    tags=["Reports"],
    summary="Retrieve a operation reports",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def operation_report(
    request: Request, dynamic: DynamicPath, operation: OperationPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "operation": operation.value})
    return await ReportRepository.get_operation_reports(
        request, dynamic, operation
    )
