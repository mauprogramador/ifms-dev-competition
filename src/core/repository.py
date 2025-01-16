from datetime import datetime
from http import HTTPStatus
from sqlite3 import OperationalError, connect

from fastapi import HTTPException, Request

from src.api.presenters import SuccessJSON
from src.common.enums import Dynamic
from src.common.types import Exchange
from src.core.config import LOG
from src.utils.functions import format_report


class Repository:
    __DATABASE = "database.db"
    __CREATE_TABLE = """CREATE TABLE IF NOT EXISTS report (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dynamic TEXT NOT NULL,
        code TEXT NOT NULL,
        type_in TEXT NOT NULL,
        type_out TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );"""
    __INSERT = (
        "INSERT INTO report(dynamic,code,type_in,type_out,timestamp)"
        " VALUES(?, ?, ?, ?, ?)"
    )
    __SELECT_DYNAMIC_REPORT = (
        "SELECT * FROM report WHERE dynamic=? ORDER BY timestamp ASC"
    )

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
    def add_report(cls, dynamic: Dynamic, form: Exchange) -> None:
        values = (
            dynamic.value,
            form.code,
            form.type.value,
            form.type.toggle.value,
            datetime.now().isoformat(),
        )
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(cls.__INSERT, values)
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
                connection.commit()

            LOG.info(f"{dynamic.value} reports found")
            reports = list(map(format_report, reports))

            return SuccessJSON(
                request,
                HTTPStatus.OK,
                f"{dynamic.value} reports found",
                {"count": len(reports), "reports": reports},
            )

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Failed"
            ) from error
