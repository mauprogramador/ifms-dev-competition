from tempfile import NamedTemporaryFile

from fastapi import File, UploadFile
from pydantic import BaseModel, Field, field_validator

from src.common.enums import FileType
from src.common.patterns import CODE_PATTERN, DYNAMIC_PATTERN


class RetrieveData(BaseModel):
    code: str = Field(
        description="Directory code (4 letters)",
        pattern=CODE_PATTERN,
        min_length=4,
        max_length=4,
        examples=["ABCD"],
    )
    type: FileType = Field(description="File type (HTML or CSS)")

    @field_validator("code", mode="after")
    @classmethod
    def code_to_upper(cls, code: str) -> str:
        return code.strip().upper()


class UploadData(RetrieveData):
    file: str = Field(
        description="File to upload (HTML or CSS)",
        min_length=1,
        examples=["<html>...<html>"],
    )


class CreateNewDynamic(BaseModel):
    name: str = Field(
        description="Name of the new dynamic",
        pattern=DYNAMIC_PATTERN,
        min_length=1,
        max_length=50,
        examples=["final"],
    )
    teams_number: int = Field(
        description="Number of Teams to create code dirs",
        ge=1,
        le=200,
        examples=[15],
    )

    @field_validator("name", mode="after")
    @classmethod
    def format_dynamic_name(cls, name: str) -> str:
        return name.strip().upper().replace("-", "_").replace(" ", "_")


class UploadAnswerKey(BaseModel):
    image: UploadFile | None = File(
        default=None,
        media_type="image/*",
        description="Answer-key image",
    )
    html: str | None = Field(
        default=None,
        description="Answer-key HTML",
        examples=[""],
    )
    css: str | None = Field(
        default=None,
        description="Answer-key CSS",
        examples=[""],
    )

    @field_validator("image", mode="before")
    @classmethod
    def validate_not_send_image(cls, image):
        if image == "" or isinstance(image, str):
            return None
        return image

    @property
    def fields(self) -> bool:
        return any((self.image, self.html, self.css))

    @property
    def web_fields(self) -> bool:
        return all((self.html, self.css))


async def get_temp_file():
    with NamedTemporaryFile(delete=False) as tmp_file:
        yield tmp_file
