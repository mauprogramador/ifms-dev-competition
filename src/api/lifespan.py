from contextlib import asynccontextmanager


from fastapi import FastAPI

from src.core.config import LOG, WEB_DRIVER
from src.repository import BaseRepository


@asynccontextmanager
async def lifespan(_: FastAPI):

    BaseRepository.create_tables()

    yield

    LOG.info("\033[33mStoping Web Driver and Multiprocess Pool")

    WEB_DRIVER.quit()

    # POOL.close()
    # POOL.join()
