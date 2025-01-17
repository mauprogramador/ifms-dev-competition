from datetime import datetime
from functools import lru_cache
from typing import Any

from src.common.enums import Operation
from src.core.config import ERROR_MESSAGE


@lru_cache(maxsize=30)
def format_dynamic_report(report: tuple) -> dict[str, Any]:
    timestamp = datetime.fromtimestamp(report[6])

    return {
        "id": report[0],
        "dynamic": report[1],
        "code": report[2],
        "operation": report[3],
        "type_in": report[4],
        "type_out": report[5],
        "timestamp": timestamp.isoformat(),
    }


@lru_cache(maxsize=30)
def set_operation_to_all(report: tuple) -> tuple:
    report_list = list(report)
    report_list[1] = Operation.ALL.value
    return tuple(report_list)


@lru_cache(maxsize=30)
def format_operation_report(report: tuple) -> dict[str, Any]:
    first = datetime.fromtimestamp(report[3])
    last = datetime.fromtimestamp(report[4])

    time_count = last - first

    hours, remainder = divmod(time_count.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    elapsed_time = (
        f"T{int(hours):02d}:{int(minutes):02d}:"
        f"{int(seconds):02d}.{time_count.microseconds:02d}"
    )

    return {
        "code": report[0],
        "operation": report[1],
        "total_exchanges": report[2],
        "first_timestamp": first.isoformat(),
        "last_timestamp": last.isoformat(),
        "elapsed_time": elapsed_time,
    }


def format_file_report(report: tuple) -> dict[str, str]:
    last = datetime.fromtimestamp(report[0])
    return {"last_timestamp": last.isoformat()}


def get_error_message(exc: Exception) -> str:
    return exc.args[0] if exc.args[0] else ERROR_MESSAGE


def format_error(exc: Exception, message: str = None) -> str:
    if message is None:
        message = get_error_message(exc)

    return f"{type(exc).__name__}: {message}"
