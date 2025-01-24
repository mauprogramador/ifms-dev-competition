from http import HTTPStatus
from io import BytesIO
from os import listdir, makedirs
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
from numpy import array
from PIL import Image
from skimage.metrics import structural_similarity

from src.api.presenters import SuccessJSON
from src.common.enums import WebFile
from src.common.params import (
    CreateNewDynamic,
    ExchangeRetrieve,
    ExchangeUpload,
)
from src.core.config import (
    ANSWER_KEY_FILENAME,
    ENV,
    IMG_DIR,
    LOG,
    WEB_DIR,
    WEB_DRIVER,
)
from src.core.repository import Repository


class UseCases:
    """Handles all request processing"""

    @staticmethod
    async def lock_requests(request: Request, dynamic: str) -> SuccessJSON:
        """Lock sending requests of a dynamic"""

        try:
            request.app.state.lock_requests[dynamic] = True
        except KeyError as error:
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"Dynamic {dynamic} not found in State"
            ) from error

        lock_requests = request.app.state.lock_requests[dynamic]
        LOG.info(f"{dynamic} requests locked. State set to {lock_requests}")

        return SuccessJSON(
            request,
            f"{dynamic} requests locked. State set to {lock_requests}",
            {"lock_requests": lock_requests},
        )

    @staticmethod
    async def unlock_requests(request: Request, dynamic: str) -> SuccessJSON:
        """Unlock sending requests of a dynamic"""

        try:
            request.app.state.lock_requests[dynamic] = False
        except KeyError as error:
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"Dynamic {dynamic} not found in State"
            ) from error

        lock_requests = request.app.state.lock_requests[dynamic]
        LOG.info(f"{dynamic} requests unlocked. State set to {lock_requests}")

        return SuccessJSON(
            request,
            f"{dynamic} requests unlocked. State set to {lock_requests}",
            {"lock_requests": lock_requests},
        )

    @staticmethod
    async def set_weight(request: Request, weight: float) -> SuccessJSON:
        """Sets the weight of the score calculation"""

        request.app.state.weight = weight
        LOG.info(f"Weight state set to {weight}")

        return SuccessJSON(
            request,
            f"Weight state set to {weight}",
            {"weight": request.app.state.weight},
        )

    @staticmethod
    async def save_answer_key(
        request: Request, dynamic: str, file: UploadFile
    ) -> SuccessJSON:
        """Saves a dynamic answer key image"""

        try:
            makedirs(IMG_DIR, exist_ok=True)
            dynamic_dir = join(IMG_DIR, dynamic)

            makedirs(dynamic_dir, exist_ok=True)
            file_path = join(dynamic_dir, ANSWER_KEY_FILENAME)

            content = await file.read()
            image = Image.open(BytesIO(content))
            image.save(file_path, format="PNG")

            WEB_DRIVER.set_window_size(image.width, image.height)

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
    async def clean_all(request: Request) -> SuccessJSON:
        """Removes all test data"""

        try:
            for dynamic_dir in listdir(WEB_DIR):
                rmtree(join(WEB_DIR, dynamic_dir))
        except OSError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in cleaning {WEB_DIR} dir",
            ) from error

        try:
            for image_dir in listdir(IMG_DIR):
                rmtree(join(IMG_DIR, image_dir))
        except OSError as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in cleaning {IMG_DIR} dir",
            ) from error

        try:
            timestamp = strftime("%Y-%m-%d_%H%-M-%S")
            file = splitext(ENV.database_file)

            backup_file = f"{file[0]}_{timestamp}{file[1]}"
            copy2(ENV.database_file, backup_file)

            Repository.clean_table()
            request.app.state.lock_requests = {}

            LOG.info("Database file backup created successfully")

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Error in making the database file backup",
            ) from error

        LOG.info("All test data has been removed")

        return SuccessJSON(request, "All test data has been removed")

    @staticmethod
    async def list_dynamics(request: Request) -> SuccessJSON:
        """Lists all Dynamics and its teams code dirs"""

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
        """Adds a new Dynamic and its teams code dirs"""

        try:
            dynamic_dir_path = join(WEB_DIR, form.name)
            makedirs(dynamic_dir_path, exist_ok=True)

            dirs_count = len(listdir(dynamic_dir_path))
            count = form.teams_number - dirs_count

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

                for file in WebFile:
                    file_path = join(dir_path, file)

                    with open(file_path, mode="w", encoding="utf-8"):
                        pass

            request.app.state.lock_requests.setdefault(form.name, True)
            LOG.info(f"Dynamic {form.name} has {count} code dirs created")

        except Exception as error:
            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in creating {form.name} code dirs",
            ) from error

        return SuccessJSON(
            request,
            f"{form.name} code dirs tree created",
            {"dynamic": form.name, "count": count},
            HTTPStatus.CREATED,
        )

    @staticmethod
    async def remove_dynamic(request: Request, dynamic: str) -> SuccessJSON:
        """Removes a Dynamic and its teams code dirs"""

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

        LOG.info(f"Dynamic {dynamic} removed")

        return SuccessJSON(
            request,
            f"Dynamic {dynamic} removed",
            {"dynamic": dynamic},
        )

    @staticmethod
    async def list_code_dirs(request: Request, dynamic: str) -> SuccessJSON:
        """List a dynamic code dirs"""

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
        """Add a dynamic new code dir"""

        dynamic_dir_path = join(WEB_DIR, dynamic)

        dir_code = "".join(sample(ascii_uppercase, k=4))
        dir_path = join(dynamic_dir_path, dir_code)

        try:
            makedirs(dir_path, exist_ok=True)

            for file in WebFile:
                file_path = join(dir_path, file)

                with open(file_path, mode="w", encoding="utf-8"):
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
        """Remove a dynamic code dir"""

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
        request: Request, dynamic: str, query: ExchangeRetrieve
    ) -> SuccessJSON:
        """Retrieves a code dir file"""

        code_dir_path = join(WEB_DIR, dynamic, query.code)

        if not exists(code_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Code dir {query.code} not found",
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
        request: Request, dynamic: str, form: ExchangeUpload
    ) -> SuccessJSON:
        """Uploads a code dir file"""

        code_dir_path = join(WEB_DIR, dynamic, form.code)

        if not exists(code_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"Code dir {form.code} not found"
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
    async def exchange_files(
        request: Request, dynamic: str, form: ExchangeUpload
    ) -> SuccessJSON:
        "Exchange files of a dynamic code dir"

        code_dir_path = join(WEB_DIR, dynamic, form.code)

        if not exists(code_dir_path):
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"Code dir  {form.code} not found"
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
            f"Code dir {form.code} exchange "
            f"{form.type.filename.value} to {filename}"
        )
        LOG.info(message)

        return SuccessJSON(
            request,
            message,
            {
                "dynamic": dynamic,
                "code": form.code,
                "type": form.type.toggle.value,
                "file": content,
            },
        )

    @staticmethod
    async def download_dir_tree(
        dynamic: str, temp_file: _TemporaryFileWrapper
    ) -> FileResponse:
        """Downloads a dynamic dir tree"""

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
    async def compare_to_answer_key(
        dynamic: str,
        code: str,
    ) -> float:

        dynamic_dir = join(WEB_DIR, dynamic, code, WebFile.HTML)
        dynamic_dir_path = Path(dynamic_dir)

        if not dynamic_dir_path.exists():
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Index.html not found in {dynamic} {code} code dir",
            )

        try:
            WEB_DRIVER.get(dynamic_dir_path.absolute().as_uri())
            WEB_DRIVER.implicitly_wait(1)
            screenshot = WEB_DRIVER.get_screenshot_as_png()

            img_dir = join(IMG_DIR, dynamic)
            makedirs(img_dir, exist_ok=True)

            filename = f"{code.lower()}_screenshot.png"
            file_path = join(img_dir, filename)

            screenshot_image = Image.open(BytesIO(screenshot))
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
            screenshot_image = screenshot_image.convert("L")
            answer_key_image = Image.open(answer_key_path).convert("L")

            if answer_key_image.size != screenshot_image.size:
                answer_key_image = answer_key_image.resize(
                    screenshot_image.size
                )
                answer_key_image.save(answer_key_path)

            ssim: float = structural_similarity(
                im1=array(answer_key_image),
                im2=array(screenshot_image),
                data_range=1.0,
                gaussian_weights=True,
                sigma=1.5,
                multichannel=True,
                use_sample_covariance=False,
            )
        except Exception as error:
            LOG.error(f"Error in handling {dynamic} {code} images to compare")

            raise HTTPException(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in handling {dynamic} {code} images to compare",
            ) from error

        LOG.info(f"Similarity of {code} to the answer-key: {ssim:.3f}")

        return ssim
