from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ratelimit import RateLimitMiddleware, Rule
from ratelimit.backends.simple import MemoryBackend
from starlette.middleware.sessions import SessionMiddleware

from src import __version__
from src.config import ENV, SECRET_KEY
from src.exceptions import BaseExceptionResponse
from src.middleware import TracingTimeExceptionHandlerMiddleware
from src.patterns import API_ROUTE_PATTERN
from src.routes import router

CONTACT = {
    "name": "@mauprogramador",
    "url": "https://github.com/mauprogramador",
    "email": "sir.silvabmauricio@gmail.com",
}
LICENSE = {
    "name": "MIT License",
    "identifier": "MIT",
    "url": (
        "https://github.com/mauprogramador/"
        "ifms-dev-competition/blob/master/LICENSE"
    ),
}
RESPONSES = {
    HTTPStatus.BAD_REQUEST: {
        "model": BaseExceptionResponse,
        "description": "Base exceptions response",
    }
}

app = FastAPI(
    debug=ENV.debug,
    title="IFMS Dev Competition",
    summary="RESTful API for managing the IFMS Development Competition",
    description="⚙ [**RESTful API**](/v1/ifms-dev-competition/api)",
    version=f"v{__version__}",
    contact=CONTACT,
    license_info=LICENSE,
    responses=RESPONSES,
)


async def from_session(_) -> tuple[str, str]:
    return "anonymous", "default"


RULE = [
    Rule(group="default", method="get", second=3, minute=150, block_time=10)
]
app.add_middleware(
    RateLimitMiddleware,
    authenticate=from_session,
    backend=MemoryBackend(),
    config={
        API_ROUTE_PATTERN: RULE,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(TracingTimeExceptionHandlerMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=None,
)


app.include_router(router)
