from pathlib import Path
from typing import Any
from unittest.mock import patch
from zipfile import ZipInfo

from src.common.enums import FileType, LockStatus, Operation
from src.core.config import ANSWER_KEY_FILENAME, IMG_DIR, WEB_DIR
from src.use_cases.admin import clean_reports
from src.use_cases.answer_key import AnswerKey

DATABASE = "tests/test_database.db"
IMAGE_PATH = "tests/test.png"

DYNAMIC = "TEST_DYNAMIC_PYTEST"

SHUTIL_COPY2_MOCK = patch(
    f"{clean_reports.__module__}.copy2",
    autospec=True,
    side_effect=None,
)
FAILED_WEB_FILES_MOCK = patch.object(
    AnswerKey,
    f"_{AnswerKey.__name__}__save_from_web_fields",
    side_effect=Exception("any"),
)

WEIGHT = 123
COUNT = 1

DYNAMIC_IMG_PATH = IMG_DIR / DYNAMIC
DYNAMIC_WEB_PATH = WEB_DIR / DYNAMIC

ANSWER_KEY_PATH = DYNAMIC_IMG_PATH / ANSWER_KEY_FILENAME

HTML_CONTENT = """
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <link href="style.css" rel="stylesheet" />
            <title>Document</title>
        </head>
        <body>
            <h1>Document</h1>
        </body>
    </html>
"""
CSS_CONTENT = """
    * {
        box-sizing: border-box;
        margin: 0;
    }

    h1 {
        text-align: center;
        color: #333;
    }
"""

FILE_TYPES_PARAMS = [FileType.HTML, FileType.CSS]

LOCK_REQUESTS_PARAMS = [
    (LockStatus.LOCK, True),
    (LockStatus.UNLOCK, False),
]

UPLOAD_FILE_PARAMS = [
    (FileType.HTML, HTML_CONTENT),
    (FileType.CSS, CSS_CONTENT),
]

OPERATION_REPORT_PARAMS = [
    (Operation.UPLOAD, 2),
    (Operation.RETRIEVE, 2),
    (Operation.ALL, 4),
]


def code_dirs_list() -> tuple[Path, ...]:
    return tuple(filter(Path.is_dir, DYNAMIC_WEB_PATH.iterdir()))


def zip_file_list(info_list: list[ZipInfo]) -> tuple[ZipInfo, ...]:
    return tuple(filter(ZipInfo.is_dir, info_list))


def report_filter(report: dict[str, Any]) -> bool:
    return (
        report["operation"] == Operation.UPLOAD
        and report["file_type"] == FileType.CSS
    )


def report_score(similarity: Any) -> int:
    return int((float(similarity) * WEIGHT) / 100)
