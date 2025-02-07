from datetime import datetime
from http import HTTPStatus
from typing import Any

from pytest import mark

from src.common.enums import Operation
from src.core.config import ROUTE_PREFIX
from tests.mocks import (
    CLIENT,
    COUNT,
    DYNAMIC,
    FILE_TYPES_PARAMS,
    OPERATION_REPORT_PARAMS,
    report_filter,
    report_score,
)


@mark.order(12)
@mark.asyncio
async def test_dynamic_report(session_data):
    code = session_data["code"]

    res = CLIENT.get(f"{ROUTE_PREFIX}/{DYNAMIC}/dynamic-report")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["count"] == 4
    assert len(res["data"]["reports"]) == 4

    reports = tuple(filter(report_filter, res["data"]["reports"]))
    report: dict[str, Any] = reports[0]
    assert report["code"] == code
    assert report["operation"] == Operation.UPLOAD
    assert report["file_type"] in FILE_TYPES_PARAMS
    assert datetime.fromisoformat(report["timestamp"])
    assert report["similarity"] is not None
    assert report["score"] == report_score(report["similarity"])


@mark.order(13)
@mark.parametrize("file_type", FILE_TYPES_PARAMS)
@mark.asyncio
async def test_file_report(session_data, file_type):
    code = session_data["code"]

    params = {"code": code, "type": file_type}
    url = f"{ROUTE_PREFIX}/{DYNAMIC}/file-report"

    res = CLIENT.get(url, params=params)
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["code"] == code
    assert res["data"]["type"] == file_type
    assert datetime.fromisoformat(res["data"]["report"]["last_timestamp"])


@mark.order(14)
@mark.parametrize("operation, exchanges", OPERATION_REPORT_PARAMS)
@mark.asyncio
async def test_operation_report(session_data, operation, exchanges):
    code = session_data["code"]

    res = CLIENT.get(f"{ROUTE_PREFIX}/{DYNAMIC}/operation-report/{operation}")
    assert res.status_code == HTTPStatus.OK

    res = res.json()
    assert res["success"] and res["code"] == HTTPStatus.OK
    assert res["data"]["count"] == COUNT
    assert len(res["data"]["reports"]) == COUNT

    report: dict[str, Any] = res["data"]["reports"][0]
    assert report["code"] == code
    assert report["total_exchanges"] == exchanges
    assert datetime.fromisoformat(report["first_timestamp"])
    assert datetime.fromisoformat(report["last_timestamp"])
    assert report["elapsed_time"]

    if operation != Operation.ALL:
        assert report["operation"] == operation

    if operation == Operation.RETRIEVE:
        assert report["similarity"] is None and report["score"] is None

    elif operation == Operation.UPLOAD:
        assert report["similarity"] is not None
        assert report["score"] == report_score(report["similarity"])
