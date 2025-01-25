from sqlite3 import OperationalError, connect

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

            LOG.info("\033[33mTables created successfully")

        except OperationalError as error:
            LOG.exception(error)
            raise OperationalError("Failed to create tables") from error
