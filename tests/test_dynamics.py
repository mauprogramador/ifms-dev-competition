# mypy: disable-error-code="index"
from http import HTTPStatus

from fastapi import HTTPException
from httpx import AsyncClient as Client
from pytest import mark, raises

from src.repository.dynamic_repository import DynamicRepository
from tests.mocks import DYNAMIC, DYNAMIC_IMG_PATH, DYNAMIC_WEB_PATH


@mark.order(2)
@mark.asyncio
async def test_list_dynamics(client: Client):
    res = await client.get("/list-dynamics")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["count"] == 1
    assert res["data"]["dynamics"] == [DYNAMIC]


@mark.order(1)
@mark.asyncio
async def test_add_dynamic(client: Client):
    body = {"name": DYNAMIC, "teams_number": 2}
    res = await client.post("/add-dynamic", data=body)
    assert res.status_code == HTTPStatus.CREATED

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.CREATED
    assert res["data"]["count"] == 2

    assert DYNAMIC_WEB_PATH.exists()
    assert DynamicRepository.get_dynamics() == [DYNAMIC]

    assert len(tuple(DYNAMIC_WEB_PATH.rglob("*.html"))) == 2
    assert len(tuple(DYNAMIC_WEB_PATH.rglob("*.css"))) == 2


@mark.order(19)
@mark.asyncio
async def test_remove_dynamic(client: Client):
    res = await client.delete("/remove-dynamic/{DYNAMIC}")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK

    assert not DYNAMIC_WEB_PATH.exists() and not DYNAMIC_IMG_PATH.exists()

    with raises(HTTPException) as error:
        DynamicRepository.get_dynamics()

    assert error.value.status_code == HTTPStatus.NOT_FOUND
    assert error.value.detail == "Dynamics not found"
