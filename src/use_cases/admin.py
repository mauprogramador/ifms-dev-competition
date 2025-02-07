from http import HTTPStatus
from pathlib import Path
from shutil import copy2
from time import strftime

from fastapi import HTTPException, Request

from src.api.presenters import HTTPError, SuccessJSON
from src.common.enums import FileType, LockStatus
from src.core.config import (
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


async def clean_reports(request: Request, dynamic: str) -> SuccessJSON:
    try:
        timestamp = strftime("%Y-%m-%d_%H-%M-%S")
        file = Path(ENV.database_file)

        backup_file = f"{file.stem}_{timestamp}{file.suffix}"
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
    dynamic_dir = WEB_DIR / dynamic

    if not dynamic_dir.exists():
        raise HTTPException(
            HTTPStatus.NOT_FOUND, f"{dynamic} dynamic WEB dir not found"
        )

    try:
        for code_dir in filter(Path.is_dir, dynamic_dir.iterdir()):

            index_path = code_dir / FileType.HTML.file
            with open(index_path, mode="w", encoding="utf-8"):
                pass

            css_path = code_dir / FileType.CSS.file
            with open(css_path, mode="w", encoding="utf-8"):
                pass

    except OSError as error:
        raise HTTPError(
            f"Error in cleaning {dynamic} dynamic WEB code dirs",
            error=error,
        ) from error

    dynamic_dir = IMG_DIR / dynamic

    if not dynamic_dir.exists():
        LOG.info(f"{dynamic} dynamic files cleaned")
        LOG.error(f"{dynamic} dynamic IMG dir not found")

        return SuccessJSON(request, f"{dynamic} dynamic files cleaned")

    try:
        for code_dir in filter(Path.is_dir, dynamic_dir.iterdir()):
            (code_dir / DIFF_FILENAME).unlink(missing_ok=True)
            (code_dir / SCREENSHOT_FILENAME).unlink(missing_ok=True)

    except OSError as error:
        raise HTTPError(
            f"Error in cleaning {dynamic} dynamic IMG code dirs",
            error=error,
        ) from error

    LOG.info(f"{dynamic} dynamic files cleaned and images removed")

    return SuccessJSON(
        request,
        f"{dynamic} dynamic files cleaned and images removed",
        {"dynamic": dynamic},
    )
