from asyncio import Lock

from playwright.async_api import Browser, Page, Playwright, async_playwright

from src.core.config import ENV


class ScreenshotService:
    _ARGS = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
    ]
    BASE_URL = f"http://{ENV.host}:{ENV.port}"
    _VIEWPORT = {"width": 1280, "height": 720}
    _PLAYWRIGHT: Playwright = None
    _BLANK_PAGE = "about:blank"
    _BROWSER: Browser = None
    _NEW_PAGE_TIMEOUT = 7000  # 7s
    _STATUS = "networkidle"
    _REQUEST_COUNTER = 0
    _PAGE: Page = None
    _FULL_PAGE = True
    _TIMEOUT = 1000  # 1s
    _LOCK = Lock()
    _TYPE = "png"

    @classmethod
    async def initialize(cls):
        async with cls._LOCK:
            cls._PLAYWRIGHT = await async_playwright().start()
            cls._BROWSER = await cls._PLAYWRIGHT.chromium.launch(
                headless=True, args=cls._ARGS
            )
            cls._PAGE = await cls._BROWSER.new_page(
                viewport=cls._VIEWPORT, base_url=cls.BASE_URL
            )

    @classmethod
    async def render(cls, static_url: str) -> bytes:
        await cls._PAGE.goto(cls._BLANK_PAGE)
        await cls._PAGE.goto(static_url, wait_until=cls._STATUS)
        await cls._PAGE.wait_for_timeout(cls._TIMEOUT)

        screenshot_bytes = await cls._PAGE.screenshot(
            full_page=cls._FULL_PAGE,
            type=cls._TYPE,
        )
        return screenshot_bytes

    @classmethod
    async def cleanup(cls):
        if not cls._PAGE.is_closed():
            await cls._PAGE.close()
        if cls._BROWSER.is_connected():
            await cls._BROWSER.close()
        await cls._PLAYWRIGHT.stop()
