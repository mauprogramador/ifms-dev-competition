from tempfile import _TemporaryFileWrapper
from typing import Annotated

from fastapi import Depends, File, Form, Path, Query, UploadFile
from pydantic import AfterValidator

from src.common.enums import LockStatus, Operation
from src.common.params import (
    CreateNewDynamic,
    RetrieveData,
    UploadData,
    get_temp_file,
)
from src.common.patterns import CODE_PATTERN, DYNAMIC_PATTERN
from src.utils.formaters import format_code, format_dynamic

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
    File(media_type="image/*", description="Answer Key image"),
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

RetrieveFileQuery = Annotated[RetrieveData, Query(description="Retrieve")]

UploadFileForm = Annotated[UploadData, Form(description="Upload")]

OperationPath = Annotated[Operation, Path(description="Operation")]

WeightQuery = Annotated[
    int,
    Query(
        description="Score calculation Weight",
        ge=1,
        le=100000,
        examples=[5000],
    ),
]

LockQuery = Annotated[
    LockStatus,
    Query(
        description="Lock/Unlock sending requests to a dynamic",
        examples=[False],
    ),
]
