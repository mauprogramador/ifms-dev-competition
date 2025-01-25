from contextlib import asynccontextmanager


from fastapi import FastAPI

from src.core.config import WEB_DRIVER
from src.repository import BaseRepository


@asynccontextmanager
async def lifespan(_: FastAPI):

    BaseRepository.create_tables()

    yield

    WEB_DRIVER.quit()
