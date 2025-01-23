from hashlib import shake_256
from http import HTTPStatus
from os.path import exists, join
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
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import AfterValidator, BaseModel, Field, field_validator

from src.common.enums import FileType, Operation
from src.common.patterns import CODE_PATTERN, DYNAMIC_PATTERN
from src.core.config import ANSWER_KEY_FILENAME, IMG_DIR, OAUTH2_SCHEME, TOKEN
from src.utils.formaters import format_code, format_dynamic


class ExchangeRetrieve(BaseModel):
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


class ExchangeUpload(ExchangeRetrieve):
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


async def verify_token(token: Annotated[str, Depends(OAUTH2_SCHEME)]) -> None:
    encoded_token = shake_256(TOKEN.encode(encoding="utf-8")).hexdigest(15)
    if token != encoded_token:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, "Invalid token")


async def verify_start(request: Request) -> None:
    if not request.app.state.start:
        raise HTTPException(
            HTTPStatus.LOCKED, "Request sending has not started yet"
        )

    answer_key_path = join(IMG_DIR, ANSWER_KEY_FILENAME)

    if not exists(answer_key_path):
        raise HTTPException(HTTPStatus.NOT_FOUND, "Answer-Key image not found")


Oauth2Token = Depends(verify_token)

HasStarted = Depends(verify_start)

LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]

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

ExchangeRetrieveQuery = Annotated[
    ExchangeRetrieve, Query(description="Retrieve")
]

ExchangeUploadForm = Annotated[ExchangeUpload, Form(description="Upload")]

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
