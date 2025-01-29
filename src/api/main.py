from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src import __version__
from src.api.lifespan import lifespan
from src.api.middleware import TracingTimeExceptionHandlerMiddleware
from src.api.presenters import ErrorResponse, SuccessResponse
from src.core.config import ENV, LIMITER, SECRET_KEY
from src.core.exception_handler import ExceptionHandler
from src.routes import (
    admin_router,
    code_dirs_router,
    dynamics_router,
    files_router,
    reports_router,
)

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
    HTTPStatus.OK: {
        "model": SuccessResponse,
        "description": "JSON success response",
    },
    HTTPStatus.BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "JSON error response",
    },
    HTTPStatus.UNPROCESSABLE_ENTITY: {
        "model": ErrorResponse,
        "description": "JSON error response",
    },
}

app = FastAPI(
    debug=ENV.debug,
    title="IFMS Dev Competition",
    summary="RESTful API for managing the IFMS Development Competition",
    description="⚙ [**RESTful API**](/v1/ifms-dev-competition/api)",
    version=f"v{__version__}",
    docs_url="/",
    exception_handlers=ExceptionHandler().handlers,
    lifespan=lifespan,
    contact=CONTACT,
    license_info=LICENSE,
    responses=RESPONSES,
)

app.state.limiter = LIMITER

app.add_middleware(TracingTimeExceptionHandlerMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(dynamics_router)
app.include_router(code_dirs_router)
app.include_router(files_router)
app.include_router(reports_router)

app.mount("/images", StaticFiles(directory="images"))
