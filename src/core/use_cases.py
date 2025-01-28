from http import HTTPStatus
from os import listdir, makedirs
from os.path import exists, join
from pathlib import Path
from random import sample
from shutil import rmtree
from string import ascii_uppercase
from tempfile import _TemporaryFileWrapper
from zipfile import ZIP_DEFLATED, ZipFile

from cv2 import (
    COLOR_BGR2GRAY,
    COLOR_GRAY2BGR,
    IMREAD_COLOR,
    INTER_CUBIC,
    THRESH_BINARY,
    absdiff,
    cvtColor,
    imdecode,
    imread,
    imwrite,
    resize,
    subtract,
    threshold,
)
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from numpy import all as np_all
from numpy import count_nonzero, frombuffer, full_like
from numpy import sum as np_sum
from numpy import uint8

from src.api.presenters import HTTPError, SuccessJSON
from src.common.enums import FileType
from src.common.params import CreateNewDynamic, RetrieveData, UploadData
from src.core.config import (
    ANSWER_KEY_FILENAME,
    DIFF_FILENAME,
    IMG_DIR,
    LOG,
    SCREENSHOT_FILENAME,
    WEB_DIR,
    WEB_DRIVER,
)
from src.repository import DynamicRepository


class UseCases:
    """Handles all request processing"""

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
            raise HTTPError(
                "Error in adding new code dir", error=error
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
            raise HTTPError(
                f"Error in removing dynamic code dir {code}", error=error
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
            raise HTTPError(
                f"Failed to compress {dynamic} dir", error=error
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

        size = DynamicRepository.get_size(dynamic)
        LOG.debug({"answer_key_size": size})

        WEB_DRIVER.set_window_position(0, 0)
        WEB_DRIVER.maximize_window()

        try:
            WEB_DRIVER.get(dynamic_dir_path.absolute().as_uri())
            WEB_DRIVER.implicitly_wait(1)
            binary_screenshot = WEB_DRIVER.get_screenshot_as_png()

        except Exception as error:
            LOG.error(f"Error in getting {dynamic} {code} screenshot")

            raise HTTPError(
                f"Error in getting {dynamic} {code} screenshot", error=error
            ) from error

        img_dir = join(IMG_DIR, dynamic, code)
        makedirs(img_dir, exist_ok=True)

        array_screenshot = frombuffer(binary_screenshot, dtype=uint8)
        screenshot = imdecode(array_screenshot, IMREAD_COLOR)

        screenshot_path = join(img_dir, SCREENSHOT_FILENAME)
        answer_key_path = join(IMG_DIR, dynamic, ANSWER_KEY_FILENAME)

        if not exists(answer_key_path):
            LOG.error("Answer-Key image not found")

            raise HTTPException(
                HTTPStatus.NOT_FOUND, "Answer-Key image not found"
            )

        try:
            answer_key = imread(answer_key_path)
            LOG.debug(
                {
                    "answer_key_shape": answer_key.shape,
                    "screenshot_shape": screenshot.shape,  # type: ignore
                }
            )

            if answer_key.shape != screenshot.shape:  # type: ignore
                LOG.error("Answer-Key and screenshot have different sizes")

                old_size = (screenshot.shape[1], screenshot.shape[0])
                LOG.info(f"Resizing screenshot from {old_size} to {size}")

                screenshot = resize(  # type: ignore
                    screenshot,
                    size,
                    interpolation=INTER_CUBIC,
                )

            imwrite(screenshot_path, screenshot)
            LOG.info(f"{dynamic} {code} screenshot saved")

            total_pixels = answer_key.shape[0] * answer_key.shape[1]
            diff = absdiff(answer_key, screenshot)  # type: ignore

            num_diff_pixels = count_nonzero(np_sum(diff, 2))
            percentage_diff: float = (num_diff_pixels / total_pixels) * 100
            similarity = 100.00 - percentage_diff

            diff = subtract(answer_key, screenshot)
            gray_diff = cvtColor(diff, COLOR_BGR2GRAY)

            diff = threshold(gray_diff, 30, 255, THRESH_BINARY)[1]
            diff = cvtColor(diff, COLOR_GRAY2BGR)
            diff[:, :, 0] = 0
            diff[:, :, 1] = 0

            black_pixels_mask = np_all(diff == 0, axis=2)
            white_image = full_like(answer_key, 255)
            diff[black_pixels_mask] = white_image[black_pixels_mask]

            diff_path = join(IMG_DIR, dynamic, code, DIFF_FILENAME)
            imwrite(diff_path, diff)

            LOG.debug(
                {
                    "total_pixels": total_pixels,
                    "num_diff_pixels": num_diff_pixels,
                }
            )

        except Exception as error:
            raise HTTPError(
                f"Error in handling {dynamic} {code} images to compare",
                error=error,
            ) from error

        LOG.info(f"Similarity of {code} to the answer-key: {similarity:.2f}%")

        return similarity
