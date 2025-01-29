from pathlib import Path
from secrets import token_hex

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from slowapi import Limiter
from slowapi.util import get_remote_address
from webdriver_manager.chrome import ChromeDriverManager

from src.core.env import EnvConfig
from src.utils.logging import Logging

# from multiprocessing import Pool


APP = "src.api.main:app"
ROUTE_PREFIX = "/v2/ifms-dev-competition/api"

WEB_DIR = Path("web")
IMG_DIR = Path("images")

DEFAULT_WEIGHT = 5000

ANSWER_KEY_FILENAME = "answer_key.png"
DIFF_FILENAME = "diff.png"
SCREENSHOT_FILENAME = "screenshot.png"

SECRET_KEY = token_hex(nbytes=16)

ENV = EnvConfig()
LOG = Logging(*ENV.log_config)

LIMITER = Limiter(key_func=get_remote_address)
LIMIT = "60/2seconds"

ERROR_MESSAGE = "Unexpected internal error occurred"

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_argument("--disable-gpu")

CHROME_DRIVER = ChromeDriverManager()

WEB_DRIVER = Chrome(
    service=Service(CHROME_DRIVER.install()),
    options=CHROME_OPTIONS,
)

WEB_DRIVER.set_window_position(0, 0)
WEB_DRIVER.maximize_window()

# POOL = Pool(processes=6)

HEADERS = [
    (
        "Content-Security-Policy",
        (
            "default-src 'self'; base-uri 'self'; connect-src 'self'; "
            "child-src 'none'; frame-src 'none'; frame-ancestors 'none'; "
            "form-action 'self'; img-src 'self' data: https://fastapi."
            "tiangolo.com/img/favicon.png; style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui."
            "css; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr"
            ".net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
        ),
    ),
    ("Cross-Origin-Opener-Policy", "same-origin"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("X-XSS-Protection", "1; mode=block"),
]
