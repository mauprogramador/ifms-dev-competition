from http import HTTPStatus
from sqlite3 import OperationalError, connect

from fastapi import HTTPException

from src.core.config import ENV, LOG
from src.repository import queries


class BaseRepository:
    __DATABASE = ENV.database_file

    @classmethod
    def create_tables(cls) -> None:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.CREATE_REPORT_TABLE)
                cursor.execute(queries.CREATE_DYNAMIC_TABLE)
                connection.commit()

            LOG.info("Tables created successfully")

        except OperationalError as error:
            LOG.exception(error)
            raise OperationalError("Failed to create tables") from error

    @classmethod
    def clean_tables(cls) -> None:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.DELETE_ALL_REPORTS)
                cursor.execute(queries.DELETE_ALL_DYNAMICS)
                connection.commit()

            LOG.info("Tables cleaned successfully")

        except OperationalError as error:
            LOG.exception(error)
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to clean tables"
            ) from error
