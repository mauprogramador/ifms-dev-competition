from http import HTTPStatus
from io import BytesIO
from os import listdir, makedirs, remove
from os.path import exists, join, splitext
from shutil import copy2
from time import strftime

from fastapi import HTTPException, Request, UploadFile
from PIL import Image

from src.api.presenters import HTTPError, SuccessJSON
from src.common.enums import FileType, LockStatus
from src.core.config import (
    ANSWER_KEY_FILENAME,
    DIFF_FILENAME,
    ENV,
    IMG_DIR,
    LOG,
    SCREENSHOT_FILENAME,
    WEB_DIR,
)
from src.repository import DynamicRepository, ReportRepository


async def lock_requests(
    request: Request, dynamic: str, lock_status: LockStatus
) -> SuccessJSON:
    DynamicRepository.set_lock_status(dynamic, lock_status.boolean)

    LOG.info(f"{dynamic} lock requests set to {lock_status.name}")

    return SuccessJSON(
        request,
        f"{dynamic} lock request set to {lock_status.name}",
        {"lock_status": lock_status.name},
    )


async def set_weight(
    request: Request, dynamic: str, weight: int
) -> SuccessJSON:
    DynamicRepository.set_weight(dynamic, weight)
    LOG.info(f"Score weight set to {weight}")

    return SuccessJSON(
        request,
        f"Score weight set to {weight}",
        {"weight": weight},
    )


async def save_answer_key(
    request: Request, dynamic: str, file: UploadFile
) -> SuccessJSON:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            "Answer-Key file must be an image",
        )

    try:
        makedirs(IMG_DIR, exist_ok=True)
        dynamic_dir = join(IMG_DIR, dynamic)

        makedirs(dynamic_dir, exist_ok=True)
        file_path = join(dynamic_dir, ANSWER_KEY_FILENAME)

        content = await file.read()
        image = Image.open(BytesIO(content))
        image.save(file_path, format="PNG")

    except Exception as error:
        raise HTTPError(
            f"Error in writing {ANSWER_KEY_FILENAME}", error=error
        ) from error

    DynamicRepository.set_size(dynamic, image.size)
    LOG.info(f"Answer-Key image {image.size} saved in PNG")

    return SuccessJSON(
        request,
        f"Answer key image {ANSWER_KEY_FILENAME} saved",
    )


async def clean_reports(request: Request, dynamic: str) -> SuccessJSON:
    try:
        timestamp = strftime("%Y-%m-%d_%H-%M-%S")
        file = splitext(ENV.database_file)

        backup_file = f"{file[0]}_{timestamp}{file[1]}"
        copy2(ENV.database_file, backup_file)

        LOG.debug({"backup_file": backup_file})

    except Exception as error:
        raise HTTPError(
            "Error in making the database file backup", error=error
        ) from error

    ReportRepository.clean_reports(dynamic)
    LOG.info("Database file backup created successfully")
    LOG.info(f"{dynamic} dynamic reports records removed")

    return SuccessJSON(
        request,
        f"{dynamic} dynamic reports records removed",
        {"dynamic": dynamic, "backup_file": backup_file},
    )


async def clean_files(request: Request, dynamic: str) -> SuccessJSON:
    dynamic_dir = join(WEB_DIR, dynamic)

    if not exists(dynamic_dir):
        raise HTTPException(
            HTTPStatus.NOT_FOUND, f"{dynamic} dynamic WEB dir not found"
        )

    try:
        for code_dir in listdir(dynamic_dir):
            index_path = join(dynamic_dir, code_dir, FileType.HTML.file)
            with open(index_path, mode="w", encoding="utf-8"):
                pass

            css_path = join(dynamic_dir, code_dir, FileType.CSS.file)
            with open(css_path, mode="w", encoding="utf-8"):
                pass

    except OSError as error:
        raise HTTPError(
            f"Error in cleaning {dynamic} dynamic WEB code dirs",
            error=error,
        ) from error

    dynamic_dir = join(IMG_DIR, dynamic)

    if not exists(dynamic_dir):
        LOG.info(f"{dynamic} dynamic files cleaned")
        LOG.error(f"{dynamic} dynamic IMG dir not found")

        return SuccessJSON(request, f"{dynamic} dynamic files cleaned")

    try:
        for code_dir in listdir(dynamic_dir):
            diff_dir = join(dynamic_dir, code_dir, DIFF_FILENAME)
            if exists(diff_dir):
                remove(diff_dir)
            screenshot_dir = join(
                dynamic_dir, code_dir, SCREENSHOT_FILENAME
            )
            if exists(screenshot_dir):
                remove(screenshot_dir)

    except OSError as error:
        raise HTTPError(
            f"Error in cleaning {dynamic} dynamic IMG code dirs",
            error=error,
        ) from error

    LOG.info(f"{dynamic} dynamic files cleaned and images removed")

    return SuccessJSON(
        request, f"{dynamic} dynamic files cleaned and images removed"
    )
