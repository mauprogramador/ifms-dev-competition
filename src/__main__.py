from os import makedirs

import fastapi  # pylint: disable=w0611 # noqa: F401
import itsdangerous  # pylint: disable=w0611 # noqa: F401
import PIL  # pylint: disable=w0611 # noqa: F401
import pydantic  # pylint: disable=w0611 # noqa: F401
import pydantic_settings  # pylint: disable=w0611 # noqa: F401
import selenium  # pylint: disable=w0611 # noqa: F401
import slowapi  # pylint: disable=w0611 # noqa: F401
import cv2  # pylint: disable=w0611 # noqa: F401
import numpy  # pylint: disable=w0611 # noqa: F401
import uvicorn
import webdriver_manager  # pylint: disable=w0611 # noqa: F401

from src.core.config import APP, ENV, HEADERS, LOG, IMG_DIR, WEB_DIR

if __name__ == "__main__":

    makedirs(WEB_DIR, exist_ok=True)
    makedirs(IMG_DIR, exist_ok=True)

    LOG.info("\033[33mIFMS Dev Competition RESTful API was initialized 🚀")
    LOG.debug(ENV.model_dump())

    uvicorn.run(
        app=APP,
        host=ENV.host,
        port=ENV.port,
        reload=ENV.reload,
        workers=ENV.workers,
        access_log=False,
        server_header=True,
        date_header=True,
        timeout_graceful_shutdown=5,
        headers=HEADERS,
        use_colors=True,
    )
