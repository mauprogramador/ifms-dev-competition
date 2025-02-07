from sqlite3 import Error, connect

from src.core.config import ENV, LOG
from src.repository import queries


class BaseRepository:
    _DATABASE = ENV.database_file

    @classmethod
    def create_tables(cls) -> None:
        try:
            with connect(cls._DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.CREATE_REPORT_TABLE)
                cursor.execute(queries.CREATE_DYNAMIC_TABLE)
                connection.commit()

            LOG.info("\033[33mTables created successfully")

        except Error as error:
            LOG.error("Failed to create tables")
            LOG.exception(error)
            raise Error("Failed to create tables") from error
