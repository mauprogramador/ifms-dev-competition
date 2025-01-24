from http import HTTPStatus
from sqlite3 import OperationalError, connect
from time import time

from fastapi import HTTPException, Request

from src.api.presenters import SuccessJSON
from src.common.enums import Operation
from src.common.params import RetrieveData, UploadData
from src.core.config import ENV, LOG
from src.utils.formaters import (
    format_dynamic_report,
    format_file_report,
    format_operation_report,
    set_operation_to_all,
)


class Repository:
    __SELECT_DYNAMIC_REPORT = (
        "SELECT * FROM Report WHERE dynamic=? ORDER BY timestamp ASC;"
    )
    __INSERT = """
        INSERT INTO Report
        (dynamic,code,operation,file_type,timestamp,similarity,score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    __SELECT_OPERATION_REPORT = """
        SELECT
            code,
            operation,
            COUNT(*) AS total_exchanges,
            MIN(timestamp) AS first_timestamp,
            MAX(timestamp) AS last_timestamp,
            MAX(similarity) AS max_comparison,
            MAX(score) AS max_score
        FROM Report WHERE dynamic=? AND operation=? GROUP BY code;
    """
    __SELECT_FILE_REPORT = """
        SELECT MAX(timestamp) AS last_timestamp
        FROM Report WHERE dynamic=? AND code=? AND file_type=?;
    """
    __SELECT_OPERATIONS_REPORT = """
        SELECT
            code,
            operation,
            COUNT(*) AS total_exchanges,
            MIN(timestamp) AS first_timestamp,
            MAX(timestamp) AS last_timestamp,
            MAX(similarity) AS max_comparison,
            MAX(score) AS max_score
        FROM Report WHERE dynamic=? GROUP BY code;
    """
    __CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS Report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynamic TEXT NOT NULL,
            code TEXT NOT NULL,
            operation TEXT NOT NULL,
            file_type TEXT NOT NULL,
            timestamp REAL NOT NULL,
            similarity REAL NULL,
            score INTEGER NULL
        );
    """
    __DELETE_ALL = "DELETE FROM Report;"
    __DATABASE = ENV.database_file

    @classmethod
    def create_table(cls) -> None:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(cls.__CREATE_TABLE)
                connection.commit()

            LOG.info("Table created successfully")

        except OperationalError as error:
            LOG.error("Failed to create table")
            LOG.exception(error)

    @classmethod
    def clean_table(cls) -> None:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(cls.__DELETE_ALL)
                connection.commit()

            LOG.info("Table cleaned successfully")

        except OperationalError as error:
            LOG.error("Failed to clean table")
            LOG.exception(error)

    @classmethod
    def add_report(
        cls,
        dynamic: str,
        data: UploadData | RetrieveData,
        operation: Operation,
        similarity: float | None = None,
        weight: float | None = None,
    ) -> None:
        score = int(similarity * weight) if similarity and weight else None

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
                cursor.execute(cls.__INSERT, params)
                connection.commit()

            LOG.info("Report added successfully")

        except OperationalError as error:
            LOG.error("Failed saving report")
            LOG.exception(error)

    @classmethod
    async def get_dynamic_reports(
        cls, request: Request, dynamic: str
    ) -> SuccessJSON:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(cls.__SELECT_DYNAMIC_REPORT, (dynamic,))
                reports = cursor.fetchall()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed getting {dynamic} report",
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
                cursor.execute(cls.__SELECT_FILE_REPORT, params)
                report = cursor.fetchone()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed getting {query.code} {query.type.value} file report",
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
            sql, params = cls.__SELECT_OPERATIONS_REPORT, (dynamic,)

        else:
            sql = cls.__SELECT_OPERATION_REPORT
            params = (dynamic, operation.value)

        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(sql, params)
                reports = cursor.fetchall()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed getting {operation.value} operation report",
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
