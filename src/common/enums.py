from enum import StrEnum, unique


@unique
class FileType(StrEnum):
    HTML = "html"
    CSS = "css"

    @property
    def file(self):
        return "index.html" if self.name == "HTML" else "style.css"


@unique
class Operation(StrEnum):
    RETRIEVE = "RETRIEVE"
    UPLOAD = "UPLOAD"
    ALL = "ALL"


@unique
class LockStatus(StrEnum):
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"

    @property
    def boolean(self) -> int:
        return 1 if self.name == "LOCK" else 0
