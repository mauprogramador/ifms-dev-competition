from http import HTTPStatus
from os import listdir, makedirs
from os.path import exists, join
from pathlib import Path
from random import sample
from shutil import rmtree
from string import ascii_uppercase
from tempfile import _TemporaryFileWrapper
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

from src.api.presenters import SuccessJSON
from src.common.enums import Dynamic, FileType, TeamsCount, WebFile
from src.common.types import Exchange
from src.core.config import LOG, ROOT_DIR
from src.core.repository import Repository


class UseCases:
    """Handles all request processing"""

    @staticmethod
    async def create_directory_tree(request: Request) -> SuccessJSON:
        """Generates the entire directory tree"""

        try:
            makedirs(ROOT_DIR, exist_ok=True)
            counts: dict[Dynamic, int] = {}

            for dynamic, count in zip(Dynamic, TeamsCount):

                dynamic_dir_path = join(ROOT_DIR, dynamic.lower())
                makedirs(dynamic_dir_path, exist_ok=True)

                dirs_count = len(listdir(dynamic_dir_path))
                count = count - dirs_count

                counts.setdefault(dynamic, count)

                if count <= 0:
                    LOG.info(f"Dynamic dir {dynamic_dir_path} already exists")
                    continue

                for _ in range(count):
                    dir_code = "".join(sample(ascii_uppercase, k=4))

                    dir_path = join(dynamic_dir_path, dir_code)
                    makedirs(dir_path, exist_ok=True)

                    for file in WebFile:
                        file_path = join(dir_path, file)

                        with open(file_path, mode="w", encoding="utf-8"):
                            pass

                LOG.info(f"{dynamic} {count} dirs created")

            return SuccessJSON(
                request,
                HTTPStatus.CREATED,
                "Dynamics tree code directories created",
                {"counts": counts},
            )

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Error in creating directory tree",
            ) from error

    @staticmethod
    async def file_exchange(
        request: Request, dynamic: Dynamic, form: Exchange
    ) -> SuccessJSON:
        "Exchange files of a dynamic code directory"

        if form.file.content_type not in FileType.get_media_types():
            raise HTTPException(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "Unsupported file type. Only HTML and CSS are allowed",
            )

        if form.file.content_type != form.type:
            raise HTTPException(
                HTTPStatus.CONFLICT,
                "Unsupported file type. Only HTML and CSS are allowed",
            )

        code_dir_path = join(ROOT_DIR, dynamic.lower(), form.code)

        if not exists(code_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"Code directory {form.code} not found"
            )

        try:
            file_path = join(code_dir_path, form.type.filename.lower())

            with open(file_path, mode="w", encoding="utf-8") as file:
                content = await form.file.read()
                file.write(content.decode(encoding="utf-8"))

            alter_type = form.type.filename.toggle
            file_path = join(code_dir_path, alter_type.lower())

            with open(file_path, mode="r", encoding="utf-8") as file:
                content = file.read()

            message = (
                f"Code directory {form.code} exchange "
                f"{form.type.filename.lower()} to {alter_type.lower()}"
            )
            LOG.info(message)

            Repository.add_report(dynamic, form)

            return SuccessJSON(
                request,
                HTTPStatus.OK,
                message,
                {
                    "code": form.code,
                    "type": form.type.toggle.value,
                    "file": content,
                },
            )

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Error in exchanging files"
            ) from error

    @staticmethod
    async def list_code_directories(
        request: Request, dynamic: Dynamic
    ) -> SuccessJSON:
        """List a dynamic code directories"""

        dynamic_dir_path = join(ROOT_DIR, dynamic.lower())

        if not exists(dynamic_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, "Root directory not found"
            )

        code_dirs = listdir(dynamic_dir_path)
        LOG.info(f"{dynamic.value} has {len(code_dirs)} code dirs")

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            f"{dynamic.value} code directories",
            {"count": len(code_dirs), dynamic.value: code_dirs},
        )

    @staticmethod
    async def add_code_directory(
        request: Request, dynamic: Dynamic
    ) -> SuccessJSON:
        """Add a dynamic new code directory"""

        dynamic_dir_path = join(ROOT_DIR, dynamic.lower())
        dir_code = "".join(sample(ascii_uppercase, k=4))

        dir_path = join(dynamic_dir_path, dir_code)
        makedirs(dir_path, exist_ok=True)

        for file in WebFile:
            file_path = join(dir_path, file)

            with open(file_path, mode="w", encoding="utf-8"):
                pass

        LOG.info(f"Code dir {dir_code} added")

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            f"New code directory {dir_code} added",
            {"code": dir_code},
        )

    @staticmethod
    async def remove_code_directory(
        request: Request, dynamic: Dynamic, code: str
    ) -> SuccessJSON:
        """Remove a dynamic code directory"""

        path = join(ROOT_DIR, dynamic.lower(), code)

        if not exists(path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Dynamic code directory {code} not found",
            )

        try:
            rmtree(path)
        except OSError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in removing dynamic code directory {code}",
            ) from error

        LOG.info(f"Code dir {code} removed")

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            f"Code directory {code} remove from {dynamic.value}",
            {"code": code},
        )

    @staticmethod
    async def download_directory_tree(
        dynamic: Dynamic, temp_file: _TemporaryFileWrapper
    ) -> FileResponse:
        """Downloads a dynamic directory tree"""
        path = join(ROOT_DIR, dynamic.lower())

        try:
            with ZipFile(
                temp_file,
                mode="w",
                compression=ZIP_DEFLATED,
                compresslevel=9,
            ) as zip_archive:

                root_dir = Path(path)

                for sub_dir in root_dir.rglob("*"):
                    arcname = sub_dir.relative_to(root_dir)
                    zip_archive.write(sub_dir, arcname=arcname)

                filename = f"{dynamic.lower()}.zip"
                disposition = f"attachment; filename={filename}"

                LOG.info(f"Zip file {filename} in {temp_file.name} temp file")

                return FileResponse(
                    path=temp_file.name,
                    status_code=HTTPStatus.OK,
                    headers={
                        "Content-Type": "application/zip; charset=utf-8",
                        "Content-Disposition": disposition,
                    },
                    media_type="application/zip",
                    filename=filename,
                )

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed to compress {dynamic.lower()} directory",
            ) from error
