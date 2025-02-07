from os import environ, remove
from shutil import rmtree
from pytest import fixture

from src.repository.base_repository import BaseRepository
from tests.mocks import (
    DATABASE,
    DYNAMIC_IMG_PATH,
    DYNAMIC_WEB_PATH,
    ENV_DB_FILE,
)


def pytest_configure():
    environ.setdefault(ENV_DB_FILE, DATABASE)


@fixture(scope="session")
def session_data():
    data = {"code": "None"}
    yield data


@fixture(scope="session", autouse=True)
def lifespan():  # pylint: disable=W0621
    print("\033[93mPytest Session Start\033[m", flush=True)

    BaseRepository.create_tables()

    yield

    rmtree(DYNAMIC_IMG_PATH, True)
    rmtree(DYNAMIC_WEB_PATH, True)

    remove(DATABASE)
    environ.pop(ENV_DB_FILE)

    print("\033[93mPytest Session Finish\033[m", flush=True)
