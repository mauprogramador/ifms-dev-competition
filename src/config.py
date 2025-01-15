from secrets import token_hex

from src.env import EnvConfig
from src.logging import Logging

APP = "src.main:app"
SECRET_KEY = token_hex(nbytes=16)

ENV = EnvConfig()
LOG = Logging(*ENV.log_config)

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
