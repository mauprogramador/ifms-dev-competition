from enum import IntEnum, StrEnum, unique


@unique
class Dynamic(StrEnum):
    FIRST = "FIRST_DYNAMIC"
    LAST = "LAST_DYNAMIC"


@unique
class CodeDirs(IntEnum):
    FIRST_DYNAMIC = 30
    LAST_DYNAMIC = 10


@unique
class WebFile(StrEnum):
    HTML = "index.html"
    CSS = "style.css"

    @property
    def toggle(self):
        return self.CSS if self.name == "HTML" else self.HTML


@unique
class FileType(StrEnum):
    HTML = "html"
    CSS = "css"

    @property
    def filename(self):
        return WebFile.HTML if self.name == "HTML" else WebFile.CSS

    @property
    def toggle(self):
        return self.CSS if self.name == "HTML" else self.HTML


@unique
class Operation(StrEnum):
    RETRIEVE = "RETRIEVE"
    UPLOAD = "UPLOAD"
    EXCHANGE = "EXCHANGE"
    ALL = "ALL"
