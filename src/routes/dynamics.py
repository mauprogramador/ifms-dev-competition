from http import HTTPStatus

from fastapi import Request
from fastapi.routing import APIRouter

from src.api.presenters import SuccessJSON, SuccessResponse
from src.common.params import DynamicPath, NewDynamicForm
from src.core.config import LOG, ROUTE_PREFIX
from src.use_cases.dynamics import add_dynamic, list_dynamics, remove_dynamic

router = APIRouter(prefix=ROUTE_PREFIX, tags=["Dynamics"])


@router.get(
    "/list-dynamics",
    status_code=HTTPStatus.OK,
    summary="Lists all Dynamics and its teams code dirs",
    response_model=SuccessResponse,
)
async def api_list_dynamics(request: Request) -> SuccessJSON:
    return await list_dynamics(request)


@router.post(
    "/add-dynamic",
    status_code=HTTPStatus.OK,
    summary="Adds a new Dynamic and its teams code dirs",
    response_model=SuccessResponse,
)
async def api_add_dynamic(
    request: Request, form: NewDynamicForm
) -> SuccessJSON:
    LOG.debug(form.model_dump())
    return await add_dynamic(request, form)


@router.delete(
    "/remove-dynamic/{dynamic}",
    status_code=HTTPStatus.OK,
    summary="Removes a Dynamic and its teams code dirs",
    response_model=SuccessResponse,
)
async def api_remove_dynamic(
    request: Request, dynamic: DynamicPath
) -> SuccessJSON:
    LOG.debug({"dynamic": dynamic})
    return await remove_dynamic(request, dynamic)
