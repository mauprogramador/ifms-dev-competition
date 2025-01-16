from enum import IntEnum, StrEnum, unique


@unique
class Dynamic(StrEnum):
    FIRST = "FIRST_DINAMIC"
    LAST = "LAST_DINAMIC"


@unique
class TeamsCount(IntEnum):
    FIRST = 30
    LAST = 10


@unique
class WebFile(StrEnum):
    HTML = "index.html"
    CSS = "style.css"

    @property
    def toggle(self):
        return self.CSS if self.name == "HTML" else self.HTML


@unique
class FileType(StrEnum):
    HTML = "text/html"
    CSS = "text/css"

    @classmethod
    def get_media_types(cls):
        return (cls.HTML.value, cls.CSS.value)

    @property
    def filename(self):
        return WebFile.HTML if self.name == "HTML" else WebFile.CSS

    @property
    def toggle(self):
        return self.CSS if self.name == "HTML" else self.HTML
