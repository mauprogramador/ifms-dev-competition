from enum import StrEnum, unique


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
    ALL = "ALL"


@unique
class LockStatus(StrEnum):
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"

    @property
    def boolean(self) -> int:
        return 1 if self.name == "LOCK" else 0
