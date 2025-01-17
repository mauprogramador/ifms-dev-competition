from tempfile import _TemporaryFileWrapper, NamedTemporaryFile
from typing import Annotated

from fastapi import Form, Depends, Path, Query
from pydantic import BaseModel, Field

from src.common.enums import Dynamic, FileType, Operation
from src.common.patterns import CODE_PATTERN


class ExchangeRetrieve(BaseModel):
    code: str = Field(
        description="Directory code (4 letters)",
        pattern=CODE_PATTERN,
        min_length=4,
        max_length=4,
        examples=["ABCD"],
    )
    type: FileType = Field(description="File type (HTML or CSS)")


class ExchangeUpload(ExchangeRetrieve):
    file: str = Field(
        description="File to exchange (HTML or CSS)",
        min_length=1,
        examples=["<html>...<html>"],
    )


async def get_temp_file():
    with NamedTemporaryFile(delete=False) as tmp_file:
        yield tmp_file


DynamicPath = Annotated[Dynamic, Path(description="Competition dynamic")]

CodePath = Annotated[
    str,
    Path(
        description="Directory code (4 letters)",
        min_length=4,
        max_length=4,
        pattern=CODE_PATTERN,
        examples=["ABCD"],
    ),
]

TempFile = Annotated[_TemporaryFileWrapper, Depends(get_temp_file)]

ExchangeRetrieveQuery = Annotated[
    ExchangeRetrieve, Query(description="Retrieve")
]

ExchangeUploadForm = Annotated[ExchangeUpload, Form(description="Upload")]

OperationPath = Annotated[Operation, Path(description="Operation")]
