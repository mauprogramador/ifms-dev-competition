from enum import StrEnum
from http import HTTPStatus
from json import dumps
from logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    Filter,
    Formatter,
    Logger,
    LogRecord,
    StreamHandler,
    getLogger,
)
from logging.handlers import TimedRotatingFileHandler
from os import mkdir
from os.path import exists
from re import sub
from sys import stdout

from fastapi import Request as FRequest
from requests import Request as RRequest
from uvicorn.config import LOGGING_CONFIG

from src.patterns import ANSI_ESCAPE_PATTERN


class Prefix(StrEnum):
    TRACE = "\033[34mTRACE\033[m:".ljust(17)
    DEBUG = "\033[35mDEBUG\033[m:".ljust(17)
    INFO = "\033[32mINFO\033[m:".ljust(17)
    QUOTA = "\033[35mQUOTA\033[m:".ljust(17)
    ERROR = "\033[31mERROR\033[m:".ljust(17)
    EXCEPTION = "\033[31mEXCEPTION\033[m:".ljust(17)
    CRITICAL = "\033[31mCRITICAL\033[m:".ljust(17)
    SEARCH = "\033[36mSEARCH\033[m:".ljust(17)
    ABSTRACT = "\033[36mABSTRACT\033[m:".ljust(17)


class ANSIFormatter(Formatter):
    def format(self, record) -> str:
        message = super().format(record)
        return sub(ANSI_ESCAPE_PATTERN, "", message)


class LiveReloadFilter(Filter):
    __LIVERELOAD = "/livereload"

    def filter(self, record: LogRecord) -> bool:
        return record.getMessage().find(self.__LIVERELOAD) == -1


class Logging:
    """Configure and customize application logging"""

    __TRACE = (
        "[\033[36m{host}\033[m:\033[36m{port}\033[m] \033[{color}m"
        "{method} \033[37;1m{url}\033[m \033[{color}m{code} "
        "{status_phrase} \033[m{time:.2f}s"
    )
    __UVICORN_FMT = "%(asctime)s %(levelprefix)s %(message)s"
    __COLOR = {2: "32", 3: "33", 4: "31", 5: "31"}
    __LOGGER_NAME = "ifms.dev.competition.api"
    __FMT = "%(asctime)s %(message)s"
    __DATEFMT = "%Y-%m-%d %H:%M:%S"
    __FOLDER = ".logs"

    def __init__(
        self, host: str, port: int, logging_file: bool, debug: bool
    ) -> None:
        """Configure and customize application logging"""
        self.__logger = getLogger(self.__LOGGER_NAME)
        self.__logger.addFilter(LiveReloadFilter())
        self.__host, self.__port, self.__debug = host, port, debug

        formater = {"fmt": self.__UVICORN_FMT, "datefmt": self.__DATEFMT}
        LOGGING_CONFIG["formatters"]["default"].update(formater)

        formatter = Formatter(self.__FMT, self.__DATEFMT)
        self.__stream_handler = StreamHandler(stream=stdout)
        self.__stream_handler.setFormatter(formatter)
        self.__logger.addHandler(self.__stream_handler)

        if logging_file:
            if not exists(self.__FOLDER):
                mkdir(self.__FOLDER)

            file_handler = TimedRotatingFileHandler(
                filename=f"{self.__FOLDER}/records.log",
                when="W6",
                backupCount=7,
                encoding="utf-8",
            )

            ansi_formatter = ANSIFormatter(self.__FMT, self.__DATEFMT)
            file_handler.setFormatter(ansi_formatter)

            getLogger("uvicorn").addHandler(file_handler)
            self.__logger.addHandler(file_handler)

    @property
    def logger(self) -> list[Logger]:
        return [self.__logger]

    def info(self, message: str) -> None:
        self.__logger.setLevel(INFO)
        self.__logger.info("%s %s\033[m", Prefix.INFO, message)

    def error(self, message: str) -> None:
        self.__logger.setLevel(ERROR)
        self.__logger.error("%s \033[31m%s\033[m", Prefix.ERROR, message)

    def critical(self, message: str) -> None:
        self.__logger.setLevel(CRITICAL)
        self.__logger.critical(
            "%s \033[31m%s\033[m", Prefix.CRITICAL, message, exc_info=True
        )

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
        log_prefix: Prefix,
        request: FRequest | RRequest,
        code: int,
        time: float,
    ) -> None:
        if not hasattr(request, "client") or request.client is None:
            host, port = self.__host, self.__port
        else:
            host, port = request.client.host, request.client.port

        message = self.__TRACE.format(
            host=host,
            port=port,
            color=self.__COLOR[(code // 100)],
            method=request.method,
            url=request.url,
            code=code,
            status_phrase=HTTPStatus(code).phrase,
            time=time,
        )

        self.__logger.setLevel(INFO)
        self.__logger.info("%s %s\033[m", log_prefix, message)
