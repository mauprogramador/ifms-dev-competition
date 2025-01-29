from http import HTTPStatus

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.enums import FileType, Operation
from src.common.types import (
    DynamicPath,
    RetrieveFileQuery,
    TempFile,
    UploadFileForm,
)
from src.core.config import LIMIT, LIMITER, LOG, ROUTE_PREFIX
from src.repository import ReportRepository
from src.use_cases.compare_similarity import compare_similarity
from src.use_cases.files import download_dir_tree, retrieve_file, upload_file

router = APIRouter(prefix=ROUTE_PREFIX, tags=["Files"])


# "/{dynamic}/retrieve-file",
@router.get(
    "/{dynamic}/retrieve",
    status_code=HTTPStatus.OK,
    summary="Retrieves a code dir file",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_retrieve_file(
    request: Request,
    dynamic: DynamicPath,
    query: RetrieveFileQuery,
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "query": query.model_dump()})

    response = await retrieve_file(request, dynamic, query)
    ReportRepository.add_report(dynamic, query, Operation.RETRIEVE)

    return response


# "/{dynamic}/upload-file",
@router.post(
    "/{dynamic}/upload",
    status_code=HTTPStatus.OK,
    summary="Uploads a code dir file",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def api_upload_file(
    request: Request, dynamic: DynamicPath, form: UploadFileForm
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "form": form.model_dump()})

    response = await upload_file(request, dynamic, form)
    similarity = None

    if form.type == FileType.CSS:
        try:
            similarity = await compare_similarity(dynamic, form.code)
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
async def api_download_dir_tree(
    dynamic: DynamicPath, temp_file: TempFile
) -> FileResponse:
    LOG.debug({"dynamic": dynamic, "temp_file": temp_file.name})
    return await download_dir_tree(dynamic, temp_file)
