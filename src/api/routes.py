from http import HTTPStatus

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.enums import Operation
from src.common.params import (
    AnswerKeyFile,
    CodePath,
    DynamicPath,
    ExchangeRetrieveQuery,
    ExchangeUploadForm,
    HasLock,
    NewDynamicForm,
    OperationPath,
    TempFile,
    WeightQuery,
)
from src.core.config import LIMIT, LIMITER, LOG
from src.core.repository import Repository
from src.core.use_cases import UseCases

router = APIRouter(prefix="/v2/ifms-dev-competition/api")


@router.post(
    "/lock-requests/{dynamic}",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    summary="Lock sending requests of a dynamic",
    response_model=SuccessResponse,
)
async def lock_requests(request: Request, dynamic: DynamicPath) -> SuccessJSON:
    return await UseCases.lock_requests(request, dynamic)


@router.post(
    "/unlock-requests/{dynamic}",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    summary="Unlock sending requests of a dynamic",
    response_model=SuccessResponse,
)
async def unlock_requests(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    return await UseCases.unlock_requests(request, dynamic)


@router.post(
    "/set-weight",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    summary="Sets the weight of the score calculation",
    response_model=SuccessResponse,
)
async def set_weight(request: Request, weight: WeightQuery) -> SuccessJSON:
    LOG.debug({"weight": weight})
    return await UseCases.set_weight(request, weight)


@router.post(
    "/{dynamic}/answer-key",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    summary="Saves a dynamic answer key image",
    response_model=SuccessResponse,
)
async def save_answer_key(
    request: Request, dynamic: DynamicPath, file: AnswerKeyFile
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "filename": file.filename})
    return await UseCases.save_answer_key(request, dynamic, file)


@router.delete(
    "/clean-all",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    summary="Removes all test data",
    response_model=SuccessResponse,
)
async def clean_all(request: Request) -> SuccessJSON:
    return await UseCases.clean_all(request)


@router.get(
    "/list-dynamics",
    status_code=HTTPStatus.OK,
    tags=["Dynamics"],
    summary="Lists all Dynamics and its teams code dirs",
    response_model=SuccessResponse,
)
async def list_dynamics(request: Request) -> SuccessJSON:
    return await UseCases.list_dynamics(request)


@router.post(
    "/add-dynamic",
    status_code=HTTPStatus.OK,
    tags=["Dynamics"],
    summary="Adds a new Dynamic and its teams code dirs",
    response_model=SuccessResponse,
)
async def add_dynamic(request: Request, form: NewDynamicForm) -> SuccessJSON:
    LOG.debug(form.model_dump())
    return await UseCases.add_dynamic(request, form)


@router.delete(
    "/remove-dynamic/{dynamic}",
    status_code=HTTPStatus.OK,
    tags=["Dynamics"],
    summary="Removes a Dynamic and its teams code dirs",
    response_model=SuccessResponse,
)
async def remove_dynamic(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await UseCases.remove_dynamic(request, dynamic)


# "/{dynamic}/list-code-dirs",
@router.get(
    "/{dynamic}/list",
    status_code=HTTPStatus.OK,
    tags=["Code Dirs"],
    summary="List a dynamic code dirs",
    response_model=SuccessResponse,
)
async def list_code_dirs(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await UseCases.list_code_dirs(request, dynamic)


# "/{dynamic}/add-code-dir",
@router.post(
    "/{dynamic}/add",
    status_code=HTTPStatus.OK,
    tags=["Code Dirs"],
    summary="Add a dynamic new code dir",
    response_model=SuccessResponse,
)
async def add_code_dir(request: Request, dynamic: DynamicPath) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await UseCases.add_code_dir(request, dynamic)


# "/{dynamic}/remove-code-dir/{code}",
@router.delete(
    "/{dynamic}/remove/{code}",
    status_code=HTTPStatus.OK,
    tags=["Code Dirs"],
    summary="Remove a dynamic code dir",
    response_model=SuccessResponse,
)
async def remove_code_dir(
    request: Request, dynamic: DynamicPath, code: CodePath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "code": code})
    return await UseCases.remove_code_dir(request, dynamic, code)


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
    query: ExchangeRetrieveQuery,
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "query": query.model_dump()})

    response = await UseCases.retrieve_file(request, dynamic, query)
    Repository.add_report(dynamic, query, Operation.RETRIEVE)

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
    request: Request, dynamic: DynamicPath, form: ExchangeUploadForm
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "form": form.model_dump()})

    response = await UseCases.upload_file(request, dynamic, form)
    ssim = await UseCases.compare_to_answer_key(dynamic, form.code)

    weight = request.app.state.weight
    Repository.add_report(dynamic, form, Operation.UPLOAD, ssim, weight)

    return response


# "/{dynamic}/exchange-files",
@router.put(
    "/{dynamic}/exchange",
    status_code=HTTPStatus.OK,
    tags=["Files"],
    dependencies=[HasLock],
    summary="Exchange files of a dynamic code dir",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def exchange_files(
    request: Request, dynamic: DynamicPath, form: ExchangeUploadForm
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "form": form.model_dump()})

    response = await UseCases.upload_file(request, dynamic, form)
    ssim = await UseCases.compare_to_answer_key(dynamic, form.code)

    weight = request.app.state.weight
    Repository.add_report(dynamic, form, Operation.EXCHANGE, ssim, weight)

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
    LOG.debug({"dynamic": dynamic})
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
    return await Repository.get_dynamic_reports(request, dynamic)


@router.get(
    "/{dynamic}/file-report",
    status_code=HTTPStatus.OK,
    tags=["Reports"],
    summary="Retrieve a file report",
    response_model=SuccessResponse,
)
@LIMITER.limit(LIMIT)
async def file_report(
    request: Request, dynamic: DynamicPath, query: ExchangeRetrieveQuery
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "query": query.model_dump()})
    return await Repository.get_file_report(request, dynamic, query)


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
    LOG.debug({"dynamic": dynamic, "operation": operation.name})
    return await Repository.get_operation_reports(request, dynamic, operation)
