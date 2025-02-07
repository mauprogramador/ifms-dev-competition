from http import HTTPStatus
from pathlib import Path
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
    dynamics = DynamicRepository.get_dynamics()
    LOG.info(f"Found {len(dynamics)} dynamics")

    return SuccessJSON(
        request,
        f"Found {len(dynamics)} dynamics",
        {"count": len(dynamics), "dynamics": dynamics},
    )


async def add_dynamic(request: Request, form: CreateNewDynamic) -> SuccessJSON:
    try:
        dynamic_dir = WEB_DIR / form.name
        dynamic_dir.mkdir(parents=True, exist_ok=True)

        dirs_count = len(list(filter(Path.is_dir, dynamic_dir.iterdir())))
        count = form.teams_number - dirs_count
        LOG.debug({"count": count})

        if count <= 0:
            LOG.info(f"Dynamic dir {dynamic_dir} already exists")
            raise HTTPException(
                HTTPStatus.CONFLICT,
                f"Dynamic dir for {form.name} already exists",
            )

        for _ in range(count):
            dir_code = "".join(sample(ascii_uppercase, k=4))

            dir_path = dynamic_dir / dir_code
            dir_path.mkdir(parents=True, exist_ok=True)

            index_path = dir_path / FileType.HTML.file
            with open(index_path, mode="w", encoding="utf-8"):
                pass

            css_path = dir_path / FileType.CSS.file
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
    dynamic_dir = WEB_DIR / dynamic

    if not dynamic_dir.exists():
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            f"Dynamic {dynamic} dir not found",
        )

    try:
        rmtree(dynamic_dir)
    except OSError as error:
        raise HTTPError(
            f"Error in removing dynamic dir {dynamic}", error=error
        ) from error

    DynamicRepository.remove_dynamic(dynamic)
    dynamic_dir = IMG_DIR / dynamic

    if dynamic_dir.exists():
        rmtree(dynamic_dir)

    LOG.info(f"Dynamic {dynamic} removed")

    return SuccessJSON(
        request,
        f"Dynamic {dynamic} removed",
        {"dynamic": dynamic},
    )
