from http import HTTPStatus
from os import listdir, makedirs
from os.path import exists, join
from random import sample
from shutil import rmtree
from string import ascii_uppercase

from fastapi import HTTPException, Request

from src.api.presenters import HTTPError, SuccessJSON
from src.common.enums import FileType
from src.common.params import CreateNewDynamic
from src.core.config import IMG_DIR, LOG, WEB_DIR
from src.repository import DynamicRepository


async def list_dynamics(request: Request) -> SuccessJSON:
    dynamic_dirs = listdir(WEB_DIR)
    LOG.info(f"There was {len(dynamic_dirs)} dynamics")

    return SuccessJSON(
        request,
        "All dynamics teams code dirs",
        {"count": len(dynamic_dirs), "dynamics": dynamic_dirs},
    )


async def add_dynamic(request: Request, form: CreateNewDynamic) -> SuccessJSON:
    try:
        dynamic_dir_path = join(WEB_DIR, form.name)
        makedirs(dynamic_dir_path, exist_ok=True)

        dirs_count = len(listdir(dynamic_dir_path))
        count = form.teams_number - dirs_count
        LOG.debug({"count": count})

        if count <= 0:
            LOG.info(f"Dynamic dir {dynamic_dir_path} already exists")
            raise HTTPException(
                HTTPStatus.CONFLICT,
                f"Dynamic dir for {form.name} already exists",
            )

        for _ in range(count):
            dir_code = "".join(sample(ascii_uppercase, k=4))

            dir_path = join(dynamic_dir_path, dir_code)
            makedirs(dir_path, exist_ok=True)

            index_path = join(dir_path, FileType.HTML.file)
            with open(index_path, mode="w", encoding="utf-8"):
                pass

            css_path = join(dir_path, FileType.CSS.file)
            with open(css_path, mode="w", encoding="utf-8"):
                pass

    except Exception as error:
        raise HTTPError(
            f"Error in creating {form.name} code dirs",
            error=error,
        ) from error

    DynamicRepository.add_dynamic(form.name)
    LOG.info(f"Dynamic {form.name} has {count} code dirs created")

    return SuccessJSON(
        request,
        f"{form.name} code dirs tree created",
        {"dynamic": form.name, "count": count},
        HTTPStatus.CREATED,
    )


async def remove_dynamic(request: Request, dynamic: str) -> SuccessJSON:
    dynamic_dir_path = join(WEB_DIR, dynamic)

    if not exists(dynamic_dir_path):
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            f"Dynamic {dynamic} dir not found",
        )

    try:
        rmtree(dynamic_dir_path)
    except OSError as error:
        raise HTTPError(
            f"Error in removing dynamic dir {dynamic}", error=error
        ) from error

    DynamicRepository.remove_dynamic(dynamic)
    dynamic_dir_path = join(IMG_DIR, dynamic)

    if exists(dynamic_dir_path):
        rmtree(dynamic_dir_path)

    LOG.info(f"Dynamic {dynamic} removed")

    return SuccessJSON(
        request,
        f"Dynamic {dynamic} removed",
        {"dynamic": dynamic},
    )
