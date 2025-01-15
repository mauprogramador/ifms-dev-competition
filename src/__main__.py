import fastapi  # pylint: disable=w0611 # noqa: F401
import ratelimit  # pylint: disable=w0611 # noqa: F401
import pydantic  # pylint: disable=w0611 # noqa: F401
import pydantic_settings  # pylint: disable=w0611 # noqa: F401
import uvicorn

from src.config import LOG, ENV, APP, HEADERS


if __name__ == "__main__":

    LOG.info("\033[33mIFMS Dev Competition RESTful API was initialized 🚀")
    LOG.debug(ENV.model_dump())

    uvicorn.run(
        app=APP,
        host=ENV.host,
        port=ENV.port,
        reload=ENV.reload,
        workers=ENV.workers,
        # access_log=False,
        server_header=True,
        date_header=True,
        timeout_graceful_shutdown=5,
        headers=HEADERS,
        use_colors=True,
    )
