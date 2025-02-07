from http import HTTPStatus
from io import BytesIO
from os import remove
from pathlib import Path
from shutil import copy2

from cv2 import imencode, imread
from fastapi import HTTPException
from pytest import mark, raises

from src.common.enums import FileType
from src.core.config import (
    DIFF_FILENAME,
    ENV,
    ROUTE_PREFIX,
    SCREENSHOT_FILENAME,
)
from src.repository.dynamic_repository import DynamicRepository
from src.repository.report_repository import ReportRepository
from src.utils.formaters import get_size
from tests.mocks import (
    ANSWER_KEY_PATH,
    CLIENT,
    SHUTIL_COPY2_MOCK,
    FAILED_WEB_FILES_MOCK,
    CSS_CONTENT,
    DATABASE,
    DYNAMIC,
    DYNAMIC_IMG_PATH,
    DYNAMIC_WEB_PATH,
    HTML_CONTENT,
    IMAGE_PATH,
    LOCK_REQUESTS_PARAMS,
    WEIGHT,
)


@mark.order(6)
@mark.parametrize("status, boolean", LOCK_REQUESTS_PARAMS)
@mark.asyncio
async def test_lock_requests(status, boolean):
    url = f"{ROUTE_PREFIX}/{DYNAMIC}/lock-requests"
    res = CLIENT.put(url, params={"lock_status": status})

    assert res.status_code == HTTPStatus.OK
    assert DynamicRepository.get_lock_status(DYNAMIC) is boolean

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["lock_status"] == status


@mark.order(7)
@mark.asyncio
async def test_set_weight():
    url = f"{ROUTE_PREFIX}/{DYNAMIC}/set-weight"
    res = CLIENT.put(url, params={"weight": WEIGHT})

    assert res.status_code == HTTPStatus.OK
    assert DynamicRepository.get_weight(DYNAMIC) == WEIGHT

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["weight"] == WEIGHT


@mark.order(8)
@mark.asyncio
async def test_save_answer_key_from_image():
    url = f"{ROUTE_PREFIX}/{DYNAMIC}/answer-key"
    image = imread(IMAGE_PATH)

    _, img_encoded = imencode(".png", image)
    image_bytes = img_encoded.tobytes()
    file_data = ("test.png", BytesIO(image_bytes), "image/png")

    assert not ANSWER_KEY_PATH.exists()
    res = CLIENT.post(url, files={"image": file_data})

    assert res.status_code == HTTPStatus.OK
    assert DynamicRepository.get_size(DYNAMIC) == get_size(image)

    assert ANSWER_KEY_PATH.exists()
    ANSWER_KEY_PATH.unlink(missing_ok=True)

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert tuple(res["data"]["size"]) == get_size(image)


@mark.order(9)
@mark.asyncio
async def test_save_answer_key_failed_web_files():
    url = f"{ROUTE_PREFIX}/{DYNAMIC}/answer-key"
    image = imread(IMAGE_PATH)

    _, img_encoded = imencode(".png", image)
    image_bytes = img_encoded.tobytes()

    file_data = ("test.png", BytesIO(image_bytes), "image/png")
    data = {"html": HTML_CONTENT, "css": CSS_CONTENT}

    index_path = DYNAMIC_WEB_PATH / FileType.HTML.file
    css_path = DYNAMIC_WEB_PATH / FileType.CSS.file

    assert not index_path.exists() and not css_path.exists()
    assert not ANSWER_KEY_PATH.exists()

    with FAILED_WEB_FILES_MOCK as mock:
        res = CLIENT.post(url, data=data, files={"image": file_data})
        mock.assert_called_once()

    assert res.status_code == HTTPStatus.OK
    assert DynamicRepository.get_size(DYNAMIC) == get_size(image)

    assert ANSWER_KEY_PATH.exists()
    ANSWER_KEY_PATH.unlink(missing_ok=True)

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert tuple(res["data"]["size"]) == get_size(image)


@mark.order(10)
@mark.asyncio
async def test_save_answer_key_from_web_files():
    url = f"{ROUTE_PREFIX}/{DYNAMIC}/answer-key"
    data = {"html": HTML_CONTENT, "css": CSS_CONTENT}

    index_path = DYNAMIC_WEB_PATH / FileType.HTML.file
    css_path = DYNAMIC_WEB_PATH / FileType.CSS.file

    assert not index_path.exists() and not css_path.exists()
    assert not ANSWER_KEY_PATH.exists()

    res = CLIENT.post(url, data=data)
    assert res.status_code == HTTPStatus.OK
    size = DynamicRepository.get_size(DYNAMIC)

    assert len(css_path.read_text("utf-8")) > 0
    assert len(css_path.read_text("utf-8")) > 0
    assert ANSWER_KEY_PATH.exists()

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert tuple(res["data"]["size"]) == size


@mark.order(17)
@mark.asyncio
async def test_clean_reports():
    assert len(ReportRepository.get_dynamic_reports(DYNAMIC)) > 1

    with SHUTIL_COPY2_MOCK as mock:
        res = CLIENT.delete(f"{ROUTE_PREFIX}/{DYNAMIC}/clean-reports")
        assert res.status_code == HTTPStatus.OK

        backup_file: str = mock.call_args[0][1]  # type:ignore
        mock.assert_called_once()

    file_path = f"tests/test_{backup_file}"
    copy2(DATABASE, file_path)

    assert Path(file_path).exists()
    remove(file_path)

    with raises(HTTPException) as error:
        ReportRepository.get_dynamic_reports(DYNAMIC)
        assert error.value.status_code == HTTPStatus.NOT_FOUND
        assert error.value.detail == f"{DYNAMIC} report not found"

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert Path(ENV.database_file).exists()
    assert not Path(res["data"]["backup_file"]).exists()
    assert res["data"]["backup_file"] == backup_file


@mark.order(18)
@mark.asyncio
async def test_clean_files(session_data):
    code = session_data["code"]

    web_path = DYNAMIC_WEB_PATH / code
    img_path = DYNAMIC_IMG_PATH / code

    index_path = web_path / FileType.HTML.file
    css_path = web_path / FileType.CSS.file

    diff_path = img_path / DIFF_FILENAME
    screenshot_path = img_path / SCREENSHOT_FILENAME

    assert len(index_path.read_text("utf-8")) > 0
    assert len(css_path.read_text("utf-8")) > 0
    assert diff_path.exists() and screenshot_path.exists()

    res = CLIENT.delete(f"{ROUTE_PREFIX}/{DYNAMIC}/clean-files")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert web_path.exists() and img_path.exists()

    assert len(index_path.read_text("utf-8")) == 0
    assert len(css_path.read_text("utf-8")) == 0
    assert not diff_path.exists() and not screenshot_path.exists()
