from enum import StrEnum
from http import HTTPStatus
from json import dumps
from logging import DEBUG, ERROR, INFO, Formatter, StreamHandler, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path
from re import sub
from sys import stdout

from fastapi import Request
from uvicorn.config import LOGGING_CONFIG

from src.common.patterns import ANSI_ESCAPE_PATTERN


class Prefix(StrEnum):
    TRACE = "\033[34mTRACE\033[m:".ljust(17)
    DEBUG = "\033[35mDEBUG\033[m:".ljust(17)
    INFO = "\033[32mINFO\033[m:".ljust(17)
    ERROR = "\033[31mERROR\033[m:".ljust(17)
    EXCEPTION = "\033[31mEXCEPTION\033[m:".ljust(17)


class ANSIFormatter(Formatter):
    def format(self, record) -> str:
        message = super().format(record)
        return sub(ANSI_ESCAPE_PATTERN, "", message)


class Logging:
    """Configure and customize application logging"""

    __METHOD_COLOR = {"GET": "94", "POST": "92", "PUT": "93", "DELETE": "91"}
    __TRACE = (
        "[\033[36m{host}\033[m:\033[36m{port}\033[m] \033[{method_color}m"
        "{method} \033[37;1m{url}\033[m \033[{status_color}m{code} "
        "{status_phrase} \033[m{time:.2f}s"
    )
    __UVICORN_FMT = "%(asctime)s %(levelprefix)s %(message)s"
    __STATUS_COLOR = {2: "32", 3: "33", 4: "31", 5: "31"}
    __LOGGER_NAME = "ifms.dev.competition"
    __FMT = "%(asctime)s %(message)s"
    __DATEFMT = "%Y-%m-%d %H:%M:%S"
    __DIR = Path(".logs")

    def __init__(
        self, host: str, port: int, logging_file: bool, debug: bool
    ) -> None:
        """Configure and customize application logging"""
        self.__logger = getLogger(self.__LOGGER_NAME)
        self.__host, self.__port, self.__debug = host, port, debug

        formater = {"fmt": self.__UVICORN_FMT, "datefmt": self.__DATEFMT}
        LOGGING_CONFIG["formatters"]["default"].update(formater)

        formatter = Formatter(self.__FMT, self.__DATEFMT)
        self.__stream_handler = StreamHandler(stream=stdout)
        self.__stream_handler.setFormatter(formatter)
        self.__logger.addHandler(self.__stream_handler)

        if logging_file:
            self.__DIR.mkdir(parents=True, exist_ok=True)
            filename = self.__DIR / "records_0.log"

            file_handler = RotatingFileHandler(
                filename=filename,
                mode="a",
                maxBytes=50000,
                backupCount=15,
                encoding="utf-8",
            )

            file_handler.namer = self.__namer
            ansi_formatter = ANSIFormatter(self.__FMT, self.__DATEFMT)
            file_handler.setFormatter(ansi_formatter)

            getLogger("uvicorn").addHandler(file_handler)
            self.__logger.addHandler(file_handler)

    def __namer(self, default_filename: str) -> Path:
        log_count = Path(default_filename).suffixes[1].removeprefix(".")
        return Path(default_filename).with_name(f"records_{log_count}.log")

    def info(self, message: str) -> None:
        self.__logger.setLevel(INFO)
        self.__logger.info("%s %s\033[m", Prefix.INFO, message)

    def error(self, message: str) -> None:
        self.__logger.setLevel(ERROR)
        self.__logger.error("%s \033[31m%s\033[m", Prefix.ERROR, message)

    def debug(self, data: dict) -> None:
        if self.__debug:
            self.__logger.setLevel(DEBUG)
            self.__logger.debug(
                "%s \033[33mJSON:\033[m %s", Prefix.DEBUG, dumps(data)
            )

    def exception(self, exception: Exception) -> None:
        self.__logger.setLevel(ERROR)
        self.__logger.exception(
            "%s \033[31m%s\033[m",
            Prefix.EXCEPTION,
            repr(exception),
            exc_info=True,
        )

    def trace(
        self,
        request: Request,
        code: int,
        time: float,
    ) -> None:
        host = request.client.host if request.client else self.__host
        port = request.client.port if request.client else self.__port

        message = self.__TRACE.format(
            host=host,
            port=port,
            method_color=self.__METHOD_COLOR.get(request.method, "90"),
            method=request.method,
            url=request.url,
            status_color=self.__STATUS_COLOR.get((code // 100), "30"),
            code=code,
            status_phrase=HTTPStatus(code).phrase,
            time=time,
        )

        self.__logger.setLevel(INFO)
        self.__logger.info("%s %s\033[m", Prefix.TRACE, message)
