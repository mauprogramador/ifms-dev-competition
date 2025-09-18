from http import HTTPStatus
from os import remove
from shutil import rmtree
from subprocess import DEVNULL, Popen
from time import sleep
from urllib.parse import urljoin

from httpx import ASGITransport, AsyncClient, get
from pytest import fixture
from pytest_asyncio import fixture as async_fixture
from uvloop import EventLoopPolicy, install

from src.api.main import app
from src.core.config import IMG_DIR, LOG, ROUTE_PREFIX, WEB_DIR
from src.core.screenshot_service import ScreenshotService
from src.repository.base_repository import BaseRepository
from tests.mocks import DATABASE, DYNAMIC_IMG_PATH, DYNAMIC_WEB_PATH

install()
TIMEOUT = 15
CLIENT = ("127.0.0.1", 2007)
BASE_URL = f"http://{CLIENT[0]}:{CLIENT[1]}"
TRANSPORT = ASGITransport(app=app, client=CLIENT)


@fixture(scope="session")
def session_data():
    data = {"code": "None"}
    yield data


@fixture(scope="session")
def event_loop_policy():
    return EventLoopPolicy()


@fixture(scope="session", autouse=True)
def lifespan():
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    BaseRepository.set_database(DATABASE)
    BaseRepository.create_tables()

    print("\033[93mPytest Session Start\033[m", flush=True)

    yield

    rmtree(DYNAMIC_IMG_PATH, True)
    rmtree(DYNAMIC_WEB_PATH, True)

    remove(DATABASE)
    print("\033[93mPytest Session Finish\033[m", flush=True)


@async_fixture(scope="session", loop_scope="session", name="screenshot")
async def load_screenshot_service():
    process = Popen(
        [
            "python3",
            "-m",
            "http.server",
            str(CLIENT[1]),
            "--bind",
            CLIENT[0],
            "--directory",
            ".",
        ],
        stdout=DEVNULL,
        stderr=DEVNULL,
    )
    assert process.poll() is None

    LOG.info(
        "\033[33mStarted HTTP file server process"
        f" [\033[36m{process.pid}\033[33m]"
    )
    sleep(3)

    try:
        res = get(f"{BASE_URL}/{str(WEB_DIR)}/")
        assert res.status_code == HTTPStatus.OK
    except Exception as exc:
        process.terminate()
        process.wait()
        raise RuntimeError("HTTP file server failed to start") from exc

    ScreenshotService.BASE_URL = BASE_URL
    await ScreenshotService.initialize()

    yield

    await ScreenshotService.cleanup()
    process.terminate()
    process.wait()


@async_fixture(name="client")
async def httpx_async_client(screenshot: None):  # pylint: disable=W0613
    async with AsyncClient(
        timeout=TIMEOUT,
        base_url=urljoin(BASE_URL, ROUTE_PREFIX),
        transport=TRANSPORT,
    ) as client:
        yield client
