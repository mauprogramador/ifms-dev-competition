from asyncio import Lock

from playwright.async_api import Browser, Playwright, async_playwright

from src.core.config import ENV


class ScreenshotService:
    _ARGS = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
    ]
    _BASE_URL = f"http://{ENV.host}:{ENV.port}"
    _VIEWPORT = {"width": 1280, "height": 720}
    _PLAYWRIGHT: Playwright = None
    _BROWSER: Browser = None
    _REQUEST_COUNTER = 0
    _STATUS = "networkidle"
    _FULL_PAGE = True
    _TIMEOUT = 1000
    _LOCK = Lock()
    _TYPE = "png"

    @classmethod
    async def initialize(cls):
        async with cls._LOCK:
            cls._PLAYWRIGHT = await async_playwright().start()
            cls._BROWSER = await cls._PLAYWRIGHT.chromium.launch(
                headless=True, args=cls._ARGS
            )

    @classmethod
    async def render(cls, static_url: str) -> bytes:
        page = await cls._BROWSER.new_page(
            viewport=cls._VIEWPORT, base_url=cls._BASE_URL
        )
        try:
            await page.goto(static_url, wait_until=cls._STATUS)
            await page.wait_for_timeout(cls._TIMEOUT)

            screenshot_bytes = await page.screenshot(
                full_page=cls._FULL_PAGE,
                type=cls._TYPE,
            )

        finally:
            await page.close()

        return screenshot_bytes

    @classmethod
    async def cleanup(cls):
        if cls._BROWSER.is_connected():
            await cls._BROWSER.close()
        await cls._PLAYWRIGHT.stop()
