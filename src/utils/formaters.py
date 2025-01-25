from datetime import datetime
from functools import lru_cache
from typing import Any

from src.common.enums import Operation
from src.core.config import ERROR_MESSAGE


def format_dynamic(dynamic: str) -> str:
    return dynamic.strip().upper().replace("-", "_").replace(" ", "_")


def format_code(code: str) -> str:
    return code.strip().upper()


@lru_cache(maxsize=30)
def format_dynamic_report(report: tuple) -> dict[str, Any]:
    timestamp = datetime.fromtimestamp(report[5])

    return {
        "id": report[0],
        "code": report[2],
        "operation": report[3],
        "file_type": report[4],
        "timestamp": timestamp.isoformat(),
        "similarity": report[6],
        "score": report[7],
    }


def format_file_report(report: tuple) -> dict[str, str]:
    last = datetime.fromtimestamp(report[0])
    return {"last_timestamp": last.isoformat()}


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
        "similarity": report[5],
        "score": report[6],
    }


def get_error_message(exc: Exception) -> str:
    return exc.args[0] if exc.args and exc.args[0] else ERROR_MESSAGE


def format_error(exc: Exception, message: str = None) -> str:
    if message is None:
        message = get_error_message(exc)

    return f"{type(exc).__name__}: {message}"
