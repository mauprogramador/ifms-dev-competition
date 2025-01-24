from http import HTTPStatus
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from typing import Annotated

from fastapi import (
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    UploadFile,
)
from pydantic import AfterValidator, BaseModel, Field, field_validator

from src.common.enums import FileType, Operation
from src.common.patterns import CODE_PATTERN, DYNAMIC_PATTERN
from src.utils.formaters import format_code, format_dynamic


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
        description="File to exchange (HTML or CSS)",
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


async def get_temp_file():
    with NamedTemporaryFile(delete=False) as tmp_file:
        yield tmp_file


DynamicPath = Annotated[
    Annotated[str, AfterValidator(format_dynamic)],
    Path(
        description="Competition dynamic",
        min_length=1,
        max_length=50,
        pattern=DYNAMIC_PATTERN,
    ),
]

NewDynamicForm = Annotated[
    CreateNewDynamic,
    Form(description="Add a new dynamic and its teams code dirs"),
]

AnswerKeyFile = Annotated[
    UploadFile,
    File(media_type="multipart/form-data", description="Answer Key image"),
]

CodePath = Annotated[
    Annotated[str, AfterValidator(format_code)],
    Path(
        description="Directory code (4 letters)",
        min_length=4,
        max_length=4,
        pattern=CODE_PATTERN,
        examples=["ABCD"],
    ),
]

TempFile = Annotated[_TemporaryFileWrapper, Depends(get_temp_file)]

RetrieveFileQuery = Annotated[
    RetrieveData, Query(description="Retrieve")
]

UploadFileForm = Annotated[UploadData, Form(description="Upload")]

OperationPath = Annotated[Operation, Path(description="Operation")]

WeightQuery = Annotated[
    float,
    Query(
        description="Score calculation Weight",
        ge=1,
        le=100000,
        decimal_places=3,
        examples=[5000],
    ),
]


async def verify_lock(request: Request, dynamic: DynamicPath) -> None:
    try:
        lock_requests: bool = request.app.state.lock_requests[dynamic]
    except KeyError as error:
        raise HTTPException(
            HTTPStatus.NOT_FOUND, f"Dynamic {dynamic} not found in State"
        ) from error

    if lock_requests:
        raise HTTPException(
            HTTPStatus.LOCKED, "Request sending has not started yet"
        )


HasLock = Depends(verify_lock)
