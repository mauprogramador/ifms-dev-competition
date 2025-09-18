# mypy: disable-error-code="index"
from http import HTTPStatus
from io import BytesIO
from zipfile import ZipFile

from httpx import AsyncClient as Client
from pytest import mark

from src.common.enums import FileType
from src.common.params import RetrieveData
from src.core.config import DIFF_FILENAME, SCREENSHOT_FILENAME
from src.repository.report_repository import ReportRepository
from tests.mocks import (
    DYNAMIC,
    DYNAMIC_IMG_PATH,
    DYNAMIC_WEB_PATH,
    FILE_TYPES_PARAMS,
    UPLOAD_FILE_PARAMS,
    zip_file_list,
)


@mark.order(11)
@mark.parametrize(
    "file_type, file_content", UPLOAD_FILE_PARAMS, ids=FILE_TYPES_PARAMS
)
@mark.asyncio
async def test_upload_file(
    client: Client, session_data, file_type, file_content
):
    code = session_data["code"]

    url = f"/{DYNAMIC}/upload"
    data = {"code": code, "type": file_type, "file": file_content}

    res = await client.post(url, data=data)
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["code"] == code
    assert res["data"]["type"] == file_type

    query = RetrieveData(code=code, type=file_type)
    assert ReportRepository.get_file_report(DYNAMIC, query)

    file_path = DYNAMIC_WEB_PATH / code / file_type.file
    assert file_path.exists() and len(file_path.read_text("utf-8")) > 0

    img_path = DYNAMIC_IMG_PATH / code
    diff_path = img_path / DIFF_FILENAME
    screenshot_path = img_path / SCREENSHOT_FILENAME

    if file_type == FileType.HTML:
        assert not img_path.exists()
        assert not diff_path.exists() and not screenshot_path.exists()

    elif file_type == FileType.CSS:
        assert img_path.exists()
        assert diff_path.exists() and screenshot_path.exists()


@mark.order(12)
@mark.parametrize("file_type", FILE_TYPES_PARAMS)
@mark.asyncio
async def test_retrieve_file(client: Client, session_data, file_type):
    code = session_data["code"]
    url = f"/{DYNAMIC}/retrieve"

    res = await client.get(url, params={"code": code, "type": file_type})
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["code"] == code
    assert res["data"]["type"] == file_type
    assert len(res["data"]["file"]) > 0

    query = RetrieveData(code=code, type=file_type)
    assert ReportRepository.get_file_report(DYNAMIC, query)

    file_path = DYNAMIC_WEB_PATH / code / file_type.file
    assert file_path.exists() and len(file_path.read_text("utf-8")) > 0


@mark.order(13)
@mark.asyncio
async def test_download(client: Client):
    res = await client.get(f"/{DYNAMIC}/download")
    assert res.status_code == HTTPStatus.OK
    assert res.headers["Content-Type"].count("application/zip")
    assert res.headers["Content-Disposition"].count(f"{DYNAMIC.lower()}.zip")

    with ZipFile(BytesIO(res.content), "r") as zip_archive:
        assert len(zip_archive.filelist) == 8
        assert len(zip_file_list(zip_archive.infolist())) == 2
