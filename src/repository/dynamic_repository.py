from http import HTTPStatus
from sqlite3 import OperationalError, connect

from fastapi import HTTPException

from src.core.config import DEFAULT_WEIGHT, ENV, LOG
from src.repository import queries


class DynamicRepository:
    __DATABASE = ENV.database_file

    @classmethod
    def add_dynamic(cls, dynamic: str) -> None:
        params = (dynamic, True, DEFAULT_WEIGHT)
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.INSERT_DYNAMIC, params)
                connection.commit()

            LOG.info(f"{dynamic} dynamic added successfully")

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed saving {dynamic} dynamic",
            ) from error

    @classmethod
    def remove_dynamic(cls, dynamic: str) -> None:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.DELETE_DYNAMIC, (dynamic,))
                connection.commit()

            LOG.info("Dynamic added successfully")

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed saving {dynamic} dynamic",
            ) from error

    @classmethod
    def get_lock_status(cls, dynamic: str) -> bool:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.SELECT_LOCK_STATUS, (dynamic,))
                lock = cursor.fetchone()
                connection.commit()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed getting {dynamic} lock status",
            ) from error

        LOG.info(f"Dynamic {dynamic} lock status found")

        if lock is None or len(lock) == 0:
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"{dynamic} lock status not found"
            )

        return bool(lock[0])

    @classmethod
    def set_lock_status(cls, dynamic: str, lock: int) -> None:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.UPDATE_LOCK_STATUS, (lock, dynamic))
                connection.commit()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed setting lock status for {dynamic} dynamic",
            ) from error

    @classmethod
    def get_size(cls, dynamic: str) -> tuple[int, int]:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.SELECT_SIZE, (dynamic,))
                dimensions = cursor.fetchone()
                connection.commit()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed getting {dynamic} weight",
            ) from error

        LOG.info(f"Dynamic {dynamic} weight found")

        if dimensions is None or len(dimensions) == 0 or not all(dimensions):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"{dynamic} size not found"
            )

        size = str(dimensions[0]).split("x")

        return int(size[0]), int(size[1])

    @classmethod
    def set_size(cls, dynamic: str, size: tuple[int, int]) -> None:
        dimensions = f"{size[0]}x{size[1]}"
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.UPDATE_SIZE, (dimensions, dynamic))
                connection.commit()

        except OperationalError as error:
            LOG.exception(error)
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed setting answer-key size for {dynamic} dynamic",
            ) from error

    @classmethod
    def get_weight(cls, dynamic: str) -> int:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.SELECT_WEIGHT, (dynamic,))
                weight = cursor.fetchone()
                connection.commit()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed getting {dynamic} weight",
            ) from error

        LOG.info(f"Dynamic {dynamic} weight found")

        if weight is None or len(weight) == 0 or not all(weight):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"{dynamic} weight not found"
            )

        return int(weight[0])

    @classmethod
    def set_weight(cls, dynamic: str, weight: int) -> None:
        try:
            with connect(cls.__DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute(queries.UPDATE_WEIGHT, (weight, dynamic))
                connection.commit()

        except OperationalError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed setting weight for {dynamic} dynamic",
            ) from error
