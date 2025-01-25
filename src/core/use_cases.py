from http import HTTPStatus
from io import BytesIO
from os import listdir, makedirs, remove
from os.path import exists, join, splitext
from pathlib import Path
from random import sample
from shutil import copy2, rmtree
from string import ascii_uppercase
from tempfile import _TemporaryFileWrapper
from time import strftime
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from numpy import array, count_nonzero
from numpy import sum as sum_array
from PIL import Image
from cv2 import (
    COLOR_RGB2BGR,
    INTER_CUBIC,
    cvtColor,
    imread,
    imwrite,
    absdiff,
    resize,
)

from src.api.presenters import SuccessJSON
from src.common.enums import LockStatus, FileType
from src.common.params import (
    CreateNewDynamic,
    RetrieveData,
    UploadData,
)
from src.core.config import (
    ANSWER_KEY_FILENAME,
    DIFF_FILENAME,
    ENV,
    IMG_DIR,
    LOG,
    SCREENSHOT_FILENAME,
    WEB_DIR,
    WEB_DRIVER,
)
from src.repository import DynamicRepository
from src.repository.report_repository import ReportRepository


class UseCases:
    """Handles all request processing"""

    @staticmethod
    async def lock_requests(
        request: Request, dynamic: str, lock_requests: LockStatus
    ) -> SuccessJSON:
        DynamicRepository.set_lock_status(dynamic, lock_requests.boolean)

        LOG.info(f"{dynamic} lock requests set to {lock_requests.name}")

        return SuccessJSON(
            request,
            f"{dynamic} lock request set to {lock_requests.name}",
            {"lock_requests": lock_requests.name},
        )

    @staticmethod
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

    @staticmethod
    async def save_answer_key(
        request: Request, dynamic: str, file: UploadFile
    ) -> SuccessJSON:
        try:
            makedirs(IMG_DIR, exist_ok=True)
            dynamic_dir = join(IMG_DIR, dynamic)

            makedirs(dynamic_dir, exist_ok=True)
            file_path = join(dynamic_dir, ANSWER_KEY_FILENAME)

            content = await file.read()
            image = Image.open(BytesIO(content))
            image.save(file_path, format="PNG")

            DynamicRepository.set_size(dynamic, image.size)

            LOG.info(f"Answer-Key image {image.size} saved in PNG")

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in writing {ANSWER_KEY_FILENAME}",
            ) from error

        return SuccessJSON(
            request,
            f"Answer key image {ANSWER_KEY_FILENAME} saved",
        )

    @staticmethod
    async def clean_reports(request: Request, dynamic: str) -> SuccessJSON:
        try:
            timestamp = strftime("%Y-%m-%d_%H-%M-%S")
            file = splitext(ENV.database_file)

            backup_file = f"{file[0]}_{timestamp}{file[1]}"
            copy2(ENV.database_file, backup_file)

            LOG.debug({"backup_file": backup_file})
            ReportRepository.clean_reports(dynamic)

            LOG.info("Database file backup created successfully")

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Error in making the database file backup",
            ) from error

        LOG.info(f"{dynamic} dynamic reports records removed")

        return SuccessJSON(
            request,
            f"{dynamic} dynamic reports records removed",
            {"dynamic": dynamic, "backup_file": backup_file},
        )

    @staticmethod
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in cleaning {dynamic} dynamic WEB code dirs",
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in cleaning {dynamic} dynamic IMG code dirs",
            ) from error

        LOG.info(f"{dynamic} dynamic files cleaned and images removed")

        return SuccessJSON(
            request, f"{dynamic} dynamic files cleaned and images removed"
        )

    @staticmethod
    async def list_dynamics(request: Request) -> SuccessJSON:
        dynamic_dirs = listdir(WEB_DIR)
        LOG.info(f"There was {len(dynamic_dirs)} dynamics")

        return SuccessJSON(
            request,
            "All dynamics teams code dirs",
            {"count": len(dynamic_dirs), "dynamics": dynamic_dirs},
        )

    @staticmethod
    async def add_dynamic(
        request: Request, form: CreateNewDynamic
    ) -> SuccessJSON:
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in creating {form.name} code dirs",
            ) from error

        DynamicRepository.add_dynamic(form.name)
        LOG.info(f"Dynamic {form.name} has {count} code dirs created")

        return SuccessJSON(
            request,
            f"{form.name} code dirs tree created",
            {"dynamic": form.name, "count": count},
            HTTPStatus.CREATED,
        )

    @staticmethod
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in removing dynamic dir {dynamic}",
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

    @staticmethod
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

    @staticmethod
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Error in adding new code dir",
            ) from error

        LOG.info(f"Code dir {dir_code} added")

        return SuccessJSON(
            request,
            f"New code dir {dir_code} added",
            {"dynamic": dynamic, "code": dir_code},
        )

    @staticmethod
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in removing dynamic code dir {code}",
            ) from error

        LOG.info(f"Code dir {code} removed")

        return SuccessJSON(
            request,
            f"Code dir {code} remove from {dynamic}",
            {"dynamic": dynamic, "code": code},
        )

    @staticmethod
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in reading {query.type.file}",
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

    @staticmethod
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in writing {form.type.file}",
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

    @staticmethod
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
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed to compress {dynamic} dir",
            ) from error

    @staticmethod
    async def compare_similarity(
        dynamic: str,
        code: str,
    ) -> float:

        dynamic_dir = join(WEB_DIR, dynamic, code, FileType.HTML.file)
        dynamic_dir_path = Path(dynamic_dir)

        if not dynamic_dir_path.exists():
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Index.html not found in {dynamic} {code} code dir",
            )

        width, height = DynamicRepository.get_size(dynamic)
        LOG.debug({"answer_key_size": (width, height)})

        WEB_DRIVER.set_window_rect(0, 0, width, height)
        WEB_DRIVER.maximize_window()

        try:
            WEB_DRIVER.get(dynamic_dir_path.absolute().as_uri())
            WEB_DRIVER.implicitly_wait(1)
            screenshot = WEB_DRIVER.get_screenshot_as_png()

            img_dir = join(IMG_DIR, dynamic, code)
            makedirs(img_dir, exist_ok=True)
            file_path = join(img_dir, SCREENSHOT_FILENAME)

            screenshot_image = Image.open(BytesIO(screenshot))
            LOG.debug({"screenshot_size": screenshot_image.size})
            screenshot_image.save(file_path, format="PNG")

        except Exception as error:
            LOG.error(f"Error in getting {dynamic} {code} screenshot")

            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in getting {dynamic} {code} screenshot",
            ) from error

        LOG.info(f"{dynamic} {code} screenshot saved")

        answer_key_path = join(IMG_DIR, dynamic, ANSWER_KEY_FILENAME)

        if not exists(answer_key_path):
            LOG.error("Answer-Key image not found")

            raise HTTPException(
                HTTPStatus.NOT_FOUND, "Answer-Key image not found"
            )

        try:
            screenshot = cvtColor(array(screenshot_image), COLOR_RGB2BGR)
            answer_key = imread(answer_key_path)

            LOG.debug(
                {
                    "answer_key_shape": answer_key.shape,
                    "screenshot_shape": screenshot.shape,  # type: ignore
                }
            )

            if answer_key.shape != screenshot.shape:  # type: ignore
                screenshot = resize(  # type: ignore
                    screenshot,
                    (width, height),
                    interpolation=INTER_CUBIC,
                )
                LOG.error(
                    "Answer-Key and screenshot have different dimensions"
                )

            total_pixels = answer_key.shape[0] * answer_key.shape[1]
            diff = absdiff(answer_key, screenshot)  # type: ignore

            diff_path = join(IMG_DIR, dynamic, code, DIFF_FILENAME)
            imwrite(diff_path, diff)

            num_diff_pixels = count_nonzero(sum_array(diff, 2))
            percentage_diff: float = (num_diff_pixels / total_pixels) * 100

            LOG.debug(
                {
                    "total_pixels": total_pixels,
                    "num_diff_pixels": num_diff_pixels,
                }
            )

            similarity = 100.00 - percentage_diff

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in handling {dynamic} {code} images to compare",
            ) from error

        LOG.info(f"Similarity of {code} to the answer-key: {similarity:.2f}")

        return similarity
