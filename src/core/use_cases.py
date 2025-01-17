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
from src.common.enums import Dynamic, Operation, CodeDirs, WebFile
from src.common.params import ExchangeRetrieve, ExchangeUpload
from src.core.config import LOG, ROOT_DIR
from src.core.repository import Repository


class UseCases:
    """Handles all request processing"""

    @staticmethod
    async def create_directory_tree(request: Request) -> SuccessJSON:
        """Generates the entire directory tree"""

        try:
            makedirs(ROOT_DIR, exist_ok=True)
            counts: dict[str, int] = {}

            for code_dir in CodeDirs:

                dynamic_dir_path = join(ROOT_DIR, code_dir.name)
                makedirs(dynamic_dir_path, exist_ok=True)

                dirs_count = len(listdir(dynamic_dir_path))
                count = code_dir.value - dirs_count

                counts.setdefault(code_dir.name, count)

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

                LOG.info(f"{code_dir.name} {count} dirs created")

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
    async def retrieve_file(
        request: Request, dynamic: Dynamic, query: ExchangeRetrieve
    ) -> SuccessJSON:
        """Retrieves a code directory file"""

        code_dir_path = join(ROOT_DIR, dynamic.value, query.code)

        if not exists(code_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Code directory {query.code} not found",
            )

        filename = query.type.filename.value
        file_path = join(code_dir_path, filename)

        try:
            with open(file_path, mode="r", encoding="utf-8") as file:
                content = file.read()

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in reading {filename}",
            ) from error

        message = f"Retrieve code dir {query.code} {filename}"
        LOG.info(message)

        Repository.add_report(dynamic, query, Operation.RETRIEVE)

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            message,
            {
                "dynamic": dynamic.value,
                "code": query.code,
                "type": query.type.value,
                "file": content,
            },
        )

    @staticmethod
    async def upload_file(
        request: Request, dynamic: Dynamic, form: ExchangeUpload
    ) -> SuccessJSON:
        """Uploads a code directory file"""

        code_dir_path = join(ROOT_DIR, dynamic.value, form.code)

        if not exists(code_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"Code directory {form.code} not found"
            )

        filename = form.type.filename.value
        file_path = join(code_dir_path, filename)

        try:
            with open(file_path, mode="w", encoding="utf-8") as file:
                file.write(form.file)

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in writing {filename}",
            ) from error

        message = f"Upload code dir {form.code} {filename}"
        LOG.info(message)

        Repository.add_report(dynamic, form, Operation.UPLOAD)

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            message,
            {
                "dynamic": dynamic.value,
                "code": form.code,
                "type": form.type.value,
            },
        )

    @staticmethod
    async def file_exchange(
        request: Request, dynamic: Dynamic, form: ExchangeUpload
    ) -> SuccessJSON:
        "Exchange files of a dynamic code directory"

        code_dir_path = join(ROOT_DIR, dynamic.value, form.code)

        if not exists(code_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"Code directory {form.code} not found"
            )

        filename = form.type.filename.value
        file_path = join(code_dir_path, filename)

        try:
            with open(file_path, mode="w", encoding="utf-8") as file:
                file.write(form.file)

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in writing {filename}",
            ) from error

        filename = form.type.filename.toggle.value
        file_path = join(code_dir_path, filename)

        try:
            with open(file_path, mode="r", encoding="utf-8") as file:
                content = file.read()

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in reading {filename}",
            ) from error

        message = (
            f"Code directory {form.code} exchange "
            f"{form.type.filename.value} to {filename}"
        )
        LOG.info(message)

        Repository.add_report(dynamic, form, Operation.EXCHANGE)

        return SuccessJSON(
            request,
            HTTPStatus.OK,
            message,
            {
                "dynamic": dynamic.value,
                "code": form.code,
                "type": form.type.toggle.value,
                "file": content,
            },
        )

    @staticmethod
    async def list_code_directories(
        request: Request, dynamic: Dynamic
    ) -> SuccessJSON:
        """List a dynamic code directories"""

        dynamic_dir_path = join(ROOT_DIR, dynamic.value)

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
            {
                "dynamic": dynamic.value,
                "count": len(code_dirs),
                dynamic.value: code_dirs,
            },
        )

    @staticmethod
    async def add_code_directory(
        request: Request, dynamic: Dynamic
    ) -> SuccessJSON:
        """Add a dynamic new code directory"""

        dynamic_dir_path = join(ROOT_DIR, dynamic.value)
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
            {"dynamic": dynamic.value, "code": dir_code},
        )

    @staticmethod
    async def remove_code_directory(
        request: Request, dynamic: Dynamic, code: str
    ) -> SuccessJSON:
        """Remove a dynamic code directory"""

        code = code.upper()
        dynamic_dir_path = join(ROOT_DIR, dynamic.value, code)

        if not exists(dynamic_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Dynamic code directory {code} not found",
            )

        try:
            rmtree(dynamic_dir_path)
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
            {"dynamic": dynamic.value, "code": code},
        )

    @staticmethod
    async def download_directory_tree(
        dynamic: Dynamic, temp_file: _TemporaryFileWrapper
    ) -> FileResponse:
        """Downloads a dynamic directory tree"""
        dynamic_dir_path = join(ROOT_DIR, dynamic.value)

        try:
            with ZipFile(
                temp_file,
                mode="w",
                compression=ZIP_DEFLATED,
                compresslevel=9,
            ) as zip_archive:

                root_dir = Path(dynamic_dir_path)

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
                f"Failed to compress {dynamic.value} directory",
            ) from error
