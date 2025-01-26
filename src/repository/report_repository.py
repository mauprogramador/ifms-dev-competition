from http import HTTPStatus
from sqlite3 import Error, connect
from time import time

from fastapi import HTTPException, Request

from src.api.presenters import HTTPError, SuccessJSON
from src.common.enums import Operation
from src.common.params import RetrieveData, UploadData
from src.core.config import ENV, LOG
from src.repository import queries
from src.repository.dynamic_repository import DynamicRepository
from src.utils.formaters import (
    format_dynamic_report,
    format_file_report,
    format_operation_report,
    set_operation_to_all,
)


class ReportRepository:
    __DATABASE = ENV.database_file

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
            with connect(cls.__DATABASE) as connection:
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
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.DELETE_REPORTS, (dynamic,))
                connection.commit()

            LOG.info(f"{dynamic} reports removed")

        except Error as error:
            raise HTTPError(
                f"Failed removing {dynamic} reports", error=error
            ) from error

    @classmethod
    async def get_dynamic_reports(
        cls, request: Request, dynamic: str
    ) -> SuccessJSON:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.SELECT_DYNAMIC_REPORT, (dynamic,))
                reports = cursor.fetchall()

        except Error as error:
            raise HTTPError(
                f"Failed getting {dynamic} report", error=error
            ) from error

        LOG.info(f"{dynamic} reports found")

        if reports is None or len(reports) == 0 or not all(reports):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"{dynamic} report not found",
            )

        reports = list(map(format_dynamic_report, reports))

        return SuccessJSON(
            request,
            f"{dynamic} reports found",
            {
                "dynamic": dynamic,
                "count": len(reports),
                "reports": reports,
            },
        )

    @classmethod
    async def get_file_report(
        cls, request: Request, dynamic: str, query: RetrieveData
    ) -> SuccessJSON:
        params = (dynamic, query.code, query.type.value)

        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.SELECT_FILE_REPORT, params)
                report = cursor.fetchone()

        except Error as error:
            raise HTTPError(
                f"Failed getting {query.code} {query.type.value} file report",
                error=error,
            ) from error

        LOG.info(f"{query.code} {query.type.value} file report found")

        if report is None or len(report) == 0 or not all(report):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"{query.code} {query.type.value} file report not found",
            )

        report = format_file_report(report)

        return SuccessJSON(
            request,
            f"{query.code} {query.type.value} operation reports found",
            {
                "dynamic": dynamic,
                "code": query.code,
                "type": query.type.value,
                "report": report,
            },
        )

    @classmethod
    async def get_operation_reports(
        cls, request: Request, dynamic: str, operation: Operation
    ) -> SuccessJSON:
        if operation == Operation.ALL:
            sql, params = queries.SELECT_OPERATIONS_REPORT, (dynamic,)

        else:
            sql = queries.SELECT_OPERATION_REPORT
            params = (dynamic, operation.value)

        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(sql, params)
                reports = cursor.fetchall()

        except Error as error:
            raise HTTPError(
                f"Failed getting {operation.value} operation report",
                error=error,
            ) from error

        LOG.info(f"{operation.value} operation reports found")

        if reports is None or len(reports) == 0 or not all(reports):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Operation report {operation.value} not found",
            )

        if operation == Operation.ALL:
            reports = list(map(set_operation_to_all, reports))

        reports = list(map(format_operation_report, reports))

        return SuccessJSON(
            request,
            f"{operation.value} operation reports found",
            {
                "dynamic": dynamic,
                "count": len(reports),
                "reports": reports,
            },
        )
