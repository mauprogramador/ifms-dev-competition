from time import time
from http import HTTPStatus
from sqlite3 import OperationalError, connect

from fastapi import HTTPException, Request

from src.api.presenters import SuccessJSON
from src.common.enums import Dynamic, Operation
from src.common.params import ExchangeRetrieve, ExchangeUpload
from src.core.config import LOG
from src.utils.formater import (
    format_dynamic_report,
    format_operation_report,
    set_operation_to_all,
)


class Repository:
    __SELECT_DYNAMIC_REPORT = (
        "SELECT * FROM Report WHERE dynamic=? ORDER BY timestamp ASC"
    )
    __INSERT = """
        INSERT INTO Report (dynamic,code,operation,type_in,type_out,timestamp)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    __SELECT_OPERATION = """
        SELECT
            code,
            operation,
            COUNT(*) AS total_exchanges,
            MIN(timestamp) AS first_timestamp,
            MAX(timestamp) AS last_timestamp
        FROM Report WHERE dynamic=? AND operation=? GROUP BY code;
    """
    __SELECT_OPERATIONS = """
        SELECT
            code,
            operation,
            COUNT(*) AS total_exchanges,
            MIN(timestamp) AS first_timestamp,
            MAX(timestamp) AS last_timestamp
        FROM Report WHERE dynamic=? GROUP BY code;
    """
    __CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS Report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dynamic TEXT NOT NULL,
            code TEXT NOT NULL,
            operation TEXT NOT NULL,
            type_in TEXT NOT NULL,
            type_out TEXT NOT NULL,
            timestamp REAL NOT NULL
        );
    """
    __DATABASE = "database.db"

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
    def add_report(
        cls,
        dynamic: Dynamic,
        data: ExchangeUpload | ExchangeRetrieve,
        operation: Operation,
    ) -> None:
        if operation == Operation.RETRIEVE:
            type_in, type_out = operation.value, data.type.value

        elif operation == Operation.UPLOAD:
            type_in, type_out = data.type.value, operation.value

        else:
            type_in, type_out = data.type.value, data.type.toggle.value

        params = (
            dynamic.value,
            data.code,
            operation.value,
            type_in,
            type_out,
            time(),
        )

        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(cls.__INSERT, params)
                connection.commit()

            LOG.info("Report added successfully")

        except OperationalError as error:
            LOG.error("Failed to save report")
            LOG.exception(error)

    @classmethod
    async def get_dynamic_reports(
        cls, request: Request, dynamic: Dynamic
    ) -> SuccessJSON:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(cls.__SELECT_DYNAMIC_REPORT, (dynamic.value,))
                reports = cursor.fetchall()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed getting {dynamic.value} report",
            ) from error

        LOG.info(f"{dynamic.value} reports found")
        reports = list(map(format_dynamic_report, reports))

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            f"{dynamic.value} reports found",
            {
                "dynamic": dynamic.value,
                "count": len(reports),
                "reports": reports,
            },
        )

    @classmethod
    async def get_operation_reports(
        cls, request: Request, dynamic: Dynamic, operation: Operation
    ) -> SuccessJSON:
        if operation == Operation.ALL:
            sql, params = cls.__SELECT_OPERATIONS, (dynamic.value,)

        else:
            sql = cls.__SELECT_OPERATION
            params = (dynamic.value, operation.value)

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

        if operation == Operation.ALL:
            reports = list(map(set_operation_to_all, reports))

        reports = list(map(format_operation_report, reports))

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            f"{operation.value} operation reports found",
            {
                "dynamic": dynamic.value,
                "count": len(reports),
                "reports": reports,
            },
        )
