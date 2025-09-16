from os import remove
from shutil import rmtree
from urllib.parse import urljoin

from httpx import ASGITransport, AsyncClient
from pytest import fixture
from pytest_asyncio import fixture as async_fixture
from uvloop import EventLoopPolicy, install

from src.api.main import app
from src.core.config import IMG_DIR, ROUTE_PREFIX, WEB_DIR
from src.core.screenshot_service import ScreenshotService
from src.repository.base_repository import BaseRepository
from tests.mocks import DATABASE, DYNAMIC_IMG_PATH, DYNAMIC_WEB_PATH

install()
TIMEOUT = 15
BASE_URL = urljoin("http://127.0.0.1:123", ROUTE_PREFIX)
TRANSPORT = ASGITransport(app=app, client=("127.0.0.1", 123))


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
    await ScreenshotService.initialize()
    yield
    await ScreenshotService.cleanup()


@async_fixture(name="client")
async def httpx_async_client(screenshot: None):
    async with AsyncClient(
        timeout=TIMEOUT, base_url=BASE_URL, transport=TRANSPORT
    ) as client:
        yield client
