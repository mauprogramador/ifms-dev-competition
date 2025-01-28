from http import HTTPStatus
from os import listdir, makedirs
from os.path import exists, join
from random import sample
from shutil import rmtree
from string import ascii_uppercase

from fastapi import HTTPException, Request

from src.api.presenters import HTTPError, SuccessJSON
from src.common.enums import FileType
from src.core.config import LOG, WEB_DIR


async def list_code_dirs(request: Request, dynamic: str) -> SuccessJSON:
    dynamic_dir_path = join(WEB_DIR, dynamic)

    if not exists(dynamic_dir_path):
        raise HTTPException(HTTPStatus.NOT_FOUND, "Root dir not found")

    code_dirs = listdir(dynamic_dir_path)
    LOG.info(f"{dynamic} has {len(code_dirs)} code dirs")

    return SuccessJSON(
        request,
        f"{dynamic} code dirs",
        {
            "dynamic": dynamic,
            "count": len(code_dirs),
            "code_dirs": code_dirs,
        },
    )


async def add_code_dir(request: Request, dynamic: str) -> SuccessJSON:
    dynamic_dir_path = join(WEB_DIR, dynamic)

    dir_code = "".join(sample(ascii_uppercase, k=4))
    dir_path = join(dynamic_dir_path, dir_code)

    try:
        makedirs(dir_path, exist_ok=False)

        index_path = join(dir_path, FileType.HTML.file)
        with open(index_path, mode="w", encoding="utf-8"):
            pass

        css_path = join(dir_path, FileType.CSS.file)
        with open(css_path, mode="w", encoding="utf-8"):
            pass

    except Exception as error:
        raise HTTPError("Error in adding new code dir", error=error) from error

    LOG.info(f"Code dir {dir_code} added")

    return SuccessJSON(
        request,
        f"New code dir {dir_code} added",
        {"dynamic": dynamic, "code": dir_code},
    )


async def remove_code_dir(
    request: Request, dynamic: str, code: str
) -> SuccessJSON:
    dynamic_dir_path = join(WEB_DIR, dynamic, code)

    if not exists(dynamic_dir_path):
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            f"Dynamic code dir {code} not found",
        )

    try:
        rmtree(dynamic_dir_path)
    except OSError as error:
        raise HTTPError(
            f"Error in removing dynamic code dir {code}", error=error
        ) from error

    LOG.info(f"Code dir {code} removed")

    return SuccessJSON(
        request,
        f"Code dir {code} remove from {dynamic}",
        {"dynamic": dynamic, "code": code},
    )
