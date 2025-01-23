from http import HTTPStatus

from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.enums import Operation
from src.common.params import (
    AnswerKeyFile,
    CodePath,
    DynamicPath,
    ExchangeRetrieveQuery,
    ExchangeUploadForm,
    HasStarted,
    LoginForm,
    NewDynamicForm,
    Oauth2Token,
    OperationPath,
    TempFile,
    WeightQuery,
)
from src.core.config import LIMIT, LIMITER, LOG
from src.core.repository import Repository
from src.core.use_cases import UseCases

router = APIRouter(prefix="/v2/ifms-dev-competition/api")


@router.post(
    "/token",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    summary="Obtain an OAuth2 token",
    response_class=JSONResponse,
    include_in_schema=False,
)
async def get_oauth2_token(form: LoginForm) -> JSONResponse:
    LOG.debug({"username": form.username, "password": form.password})
    return await UseCases.get_oauth2_token(form)


@router.post(
    "/set-star",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    dependencies=[Oauth2Token],
    summary="Sets the start of the request sending",
    response_model=SuccessResponse,
)
async def set_start(request: Request) -> SuccessJSON:
    return await UseCases.set_start(request)


@router.post(
    "/set-weight",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    dependencies=[Oauth2Token],
    summary="Sets the weight of the score calculation",
    response_model=SuccessResponse,
)
async def set_weight(request: Request, weight: WeightQuery) -> SuccessJSON:
    LOG.debug({"weight": weight})
    return await UseCases.set_weight(request, weight)


@router.post(
    "/answer-key",
    status_code=HTTPStatus.OK,
    tags=["Admin"],
    dependencies=[Oauth2Token],
    summary="Uploads answer key image",
    response_model=SuccessResponse,
)
async def save_answer_key(
    request: Request, file: AnswerKeyFile
) -> SuccessJSON:
    LOG.debug({"filename": file.filename})
    return await UseCases.save_answer_key(request, file)


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
    dependencies=[Oauth2Token],
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
    dependencies=[Oauth2Token],
    summary="Removes a Dynamic and its teams code dirs",
    response_model=SuccessResponse,
)
async def remove_dynamic(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await UseCases.remove_dynamic(request, dynamic)


@router.get(
    "/{dynamic}/list-code-dirs",
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


@router.post(
    "/{dynamic}/add-code-dir",
    status_code=HTTPStatus.OK,
    tags=["Code Dirs"],
    dependencies=[Oauth2Token],
    summary="Add a dynamic new code dir",
    response_model=SuccessResponse,
)
async def add_code_dir(request: Request, dynamic: DynamicPath) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await UseCases.add_code_dir(request, dynamic)


@router.delete(
    "/{dynamic}/remove-code-dir/{code}",
    status_code=HTTPStatus.OK,
    tags=["Code Dirs"],
    dependencies=[Oauth2Token],
    summary="Remove a dynamic code dir",
    response_model=SuccessResponse,
)
async def remove_code_dir(
    request: Request, dynamic: DynamicPath, code: CodePath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic, "code": code})
    return await UseCases.remove_code_dir(request, dynamic, code)


@router.get(
    "/{dynamic}/retrieve-file",
    status_code=HTTPStatus.OK,
    tags=["Files"],
    dependencies=[HasStarted],
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


@router.post(
    "/{dynamic}/upload-file",
    status_code=HTTPStatus.OK,
    tags=["Files"],
    dependencies=[HasStarted],
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


@router.put(
    "/{dynamic}/exchange-files",
    status_code=HTTPStatus.OK,
    tags=["Files"],
    dependencies=[HasStarted],
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
    dependencies=[Oauth2Token],
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
