from http import HTTPStatus
from sqlite3 import Error, connect
from time import time
from typing import Any

from fastapi import HTTPException

from src.api.presenters import HTTPError
from src.common.enums import Operation
from src.common.params import RetrieveData, UploadData
from src.core.config import LOG
from src.repository import queries
from src.repository.base_repository import BaseRepository
from src.repository.dynamic_repository import DynamicRepository
from src.utils.formaters import (
    format_dynamic_report,
    format_file_report,
    format_operation_report,
)


class ReportRepository(BaseRepository):

    @classmethod
    def add_report(
        cls,
        dynamic: str,
        data: UploadData | RetrieveData,
        operation: Operation,
        similarity: float | None = None,
    ) -> None:
        weight = DynamicRepository.get_weight(dynamic)

        if similarity is not None:
            score = int((similarity * weight) / 100)
        else:
            score = None

        params = (
            dynamic,
            data.code,
            operation.value,
            data.type.value,
            time(),
            similarity,
            score,
        )

        try:
            with connect(cls._DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.INSERT_REPORT, params)
                connection.commit()

            LOG.info("Report added successfully")

        except Error as error:
            LOG.exception(error)
            raise HTTPError("Failed saving report", error=error) from error

    @classmethod
    def clean_reports(cls, dynamic: str) -> None:
        try:
            with connect(cls._DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.DELETE_REPORTS, (dynamic,))
                connection.commit()

            LOG.info(f"{dynamic} reports removed")

        except Error as error:
            raise HTTPError(
                f"Failed removing {dynamic} reports", error=error
            ) from error

    @classmethod
    def get_dynamic_reports(cls, dynamic: str) -> list[dict[str, Any]]:
        try:
            with connect(cls._DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.SELECT_DYNAMIC_REPORT, (dynamic,))
                reports = cursor.fetchall()

        except Error as error:
            raise HTTPError(
                f"Failed getting {dynamic} report", error=error
            ) from error

        if reports is None or len(reports) == 0 or not all(reports):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"{dynamic} report not found",
            )

        return list(map(format_dynamic_report, reports))

    @classmethod
    def get_file_report(
        cls, dynamic: str, query: RetrieveData
    ) -> dict[str, str]:
        params = (dynamic, query.code, query.type.value)

        try:
            with connect(cls._DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.SELECT_FILE_REPORT, params)
                report = cursor.fetchone()

        except Error as error:
            raise HTTPError(
                f"Failed getting {query.code} {query.type.value} file report",
                error=error,
            ) from error

        if report is None or len(report) == 0 or not all(report):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"{query.code} {query.type.value} file report not found",
            )

        return format_file_report(report)

    @classmethod
    def get_operation_reports(
        cls, dynamic: str, operation: Operation
    ) -> list[dict[str, Any]]:
        if operation == Operation.ALL:
            sql, params = queries.SELECT_OPERATIONS_REPORT, (dynamic,)

        else:
            sql = queries.SELECT_OPERATION_REPORT
            params = (dynamic, operation.value)

        try:
            with connect(cls._DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(sql, params)
                reports = cursor.fetchall()

        except Error as error:
            raise HTTPError(
                f"Failed getting {operation.value} operation report",
                error=error,
            ) from error

        if reports is None or len(reports) == 0 or not all(reports):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Operation report {operation.value} not found",
            )

        return list(map(format_operation_report, reports))
