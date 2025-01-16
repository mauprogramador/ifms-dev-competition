from tempfile import _TemporaryFileWrapper
from typing import Annotated

from fastapi import Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field

from src.common.enums import FileType
from src.common.patterns import CODE_PATTERN
from src.utils.functions import get_temp_file

CodeQuery = Annotated[
    str,
    Query(
        description="Directory code (4 letters)",
        min_length=4,
        max_length=4,
        pattern=CODE_PATTERN,
        example="ABCD",
    ),
]


class Exchange(BaseModel):
    code: str = Field(
        description="Directory code (4 letters)",
        pattern=CODE_PATTERN,
        min_length=4,
        max_length=4,
        examples=["ABCD"],
    )
    type: FileType = Field(description="File type (HTML or CSS)")
    file: UploadFile = File(description="File to exchange (HTML or CSS)")


ExchangeForm = Annotated[Exchange, Form(media_type="multipart/form-data")]

TempFile = Annotated[_TemporaryFileWrapper, Depends(get_temp_file)]
