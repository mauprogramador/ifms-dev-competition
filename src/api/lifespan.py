from contextlib import asynccontextmanager


from fastapi import FastAPI

from src.core.config import WEB_DRIVER
from src.core.repository import Repository


@asynccontextmanager
async def lifespan(_: FastAPI):

    Repository.create_table()

    yield

    WEB_DRIVER.quit()
