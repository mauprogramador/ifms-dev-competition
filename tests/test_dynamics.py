from http import HTTPStatus
from fastapi import HTTPException
from pytest import mark, raises

from src.core.config import ROUTE_PREFIX
from src.repository.dynamic_repository import DynamicRepository
from tests.mocks import CLIENT, DYNAMIC, DYNAMIC_IMG_PATH, DYNAMIC_WEB_PATH


@mark.order(2)
@mark.asyncio
async def test_list_dynamics():
    res = CLIENT.get(f"{ROUTE_PREFIX}/list-dynamics")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["count"] == 1
    assert res["data"]["dynamics"] == [DYNAMIC]


@mark.order(1)
@mark.asyncio
async def test_add_dynamic():
    body = {"name": DYNAMIC, "teams_number": 2}
    res = CLIENT.post(f"{ROUTE_PREFIX}/add-dynamic", data=body)
    assert res.status_code == HTTPStatus.CREATED

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.CREATED
    assert res["data"]["count"] == 2

    assert DYNAMIC_WEB_PATH.exists()
    assert DynamicRepository.get_dynamics() == [DYNAMIC]

    assert len(tuple(DYNAMIC_WEB_PATH.rglob("*.html"))) == 2
    assert len(tuple(DYNAMIC_WEB_PATH.rglob("*.css"))) == 2


@mark.order(17)
@mark.asyncio
async def test_remove_dynamic():
    res = CLIENT.delete(f"{ROUTE_PREFIX}/remove-dynamic/{DYNAMIC}")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK

    assert not DYNAMIC_WEB_PATH.exists() and not DYNAMIC_IMG_PATH.exists()

    with raises(HTTPException) as error:
        DynamicRepository.get_dynamics()

    assert error.value.status_code == HTTPStatus.NOT_FOUND
    assert error.value.detail == "Dynamics not found"
