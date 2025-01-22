from contextlib import asynccontextmanager
from os import makedirs

from fastapi import FastAPI

from src.core.config import IMG_DIR, WEB_DIR, WEB_DRIVER
from src.core.repository import Repository


@asynccontextmanager
async def lifespan(_: FastAPI):

    makedirs(WEB_DIR, exist_ok=True)
    makedirs(IMG_DIR, exist_ok=True)

    Repository.create_table()

    yield

    WEB_DRIVER.quit()
