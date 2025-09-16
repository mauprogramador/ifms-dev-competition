# mypy: disable-error-code="index"
from http import HTTPStatus

from httpx import AsyncClient as Client
from pytest import mark

from src.common.enums import FileType
from tests.mocks import DYNAMIC, DYNAMIC_WEB_PATH, code_dirs_list


@mark.order(4)
@mark.asyncio
async def test_list_code_dirs(client: Client):
    res = await client.get(f"/{DYNAMIC}/list")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK

    assert res["data"]["count"] == 3
    assert len(code_dirs_list()) == 3

    for path in DYNAMIC_WEB_PATH.iterdir():
        if path.is_dir():
            assert path.name in res["data"]["code_dirs"]


@mark.order(3)
@mark.asyncio
async def test_add_code_dir(client: Client, session_data):
    res = await client.post(f"/{DYNAMIC}/add")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK

    code: str = res["data"]["code"]
    session_data["code"] = code

    dir_path = DYNAMIC_WEB_PATH / code
    assert dir_path.exists()

    assert (dir_path / FileType.HTML.file).exists()
    assert (dir_path / FileType.CSS.file).exists()


@mark.order(5)
@mark.asyncio
async def test_remove_code_dir(client: Client, session_data):
    code = session_data["code"]

    res = await client.delete(f"/{DYNAMIC}/remove/{code}")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK

    assert res["data"]["code"] == code
    assert not (DYNAMIC_WEB_PATH / code).exists()

    code_dirs = code_dirs_list()
    session_data["code"] = code_dirs[0].name
