from http import HTTPStatus

from fastapi.routing import APIRouter

from src.config import LOG

router = APIRouter(prefix="/v1/ifms-dev-competition/api")


@router.get(
    "/",
    status_code=HTTPStatus.OK,
    tags=["API"],
)
async def api(params: str | None = "Hi"):
    LOG.debug({"params": params})
    return {"message": params}
