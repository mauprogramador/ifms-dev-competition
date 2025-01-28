from http import HTTPStatus
from os.path import exists, join
from pathlib import Path
from tempfile import _TemporaryFileWrapper
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

from src.api.presenters import HTTPError, SuccessJSON
from src.common.params import RetrieveData, UploadData
from src.core.config import LOG, WEB_DIR


async def retrieve_file(
    request: Request, dynamic: str, query: RetrieveData
) -> SuccessJSON:
    code_dir_path = join(WEB_DIR, dynamic, query.code)

    if not exists(code_dir_path):
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            f"Code dir {query.code} not found",
        )

    file_path = join(code_dir_path, query.type.file)

    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            content = file.read()

    except Exception as error:
        raise HTTPError(
            f"Error in reading {query.type.file}", error=error
        ) from error

    message = f"Retrieve code dir {query.code} {query.type.file}"
    LOG.info(message)

    return SuccessJSON(
        request,
        message,
        {
            "dynamic": dynamic,
            "code": query.code,
            "type": query.type.value,
            "file": content,
        },
    )


async def upload_file(
    request: Request, dynamic: str, form: UploadData
) -> SuccessJSON:
    code_dir_path = join(WEB_DIR, dynamic, form.code)

    if not exists(code_dir_path):
        raise HTTPException(
            HTTPStatus.NOT_FOUND, f"Code dir {form.code} not found"
        )

    file_path = join(code_dir_path, form.type.file)

    try:
        with open(file_path, mode="w", encoding="utf-8") as file:
            file.write(form.file)

    except Exception as error:
        raise HTTPError(
            f"Error in writing {form.type.file}", error=error
        ) from error

    message = f"Upload code dir {form.code} {form.type.file}"
    LOG.info(message)

    return SuccessJSON(
        request,
        message,
        {
            "dynamic": dynamic,
            "code": form.code,
            "type": form.type.value,
        },
    )


async def download_dir_tree(
    dynamic: str, temp_file: _TemporaryFileWrapper
) -> FileResponse:
    try:
        with ZipFile(
            temp_file,
            mode="w",
            compression=ZIP_DEFLATED,
            compresslevel=9,
        ) as zip_archive:

            dynamic_dir = join(WEB_DIR, dynamic)
            dynamic_dir_path = Path(dynamic_dir)

            for sub_dir in dynamic_dir_path.rglob("*"):
                arcname = sub_dir.relative_to(dynamic_dir_path)
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
        raise HTTPError(
            f"Failed to compress {dynamic} dir", error=error
        ) from error
