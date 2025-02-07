from http import HTTPStatus

from cv2 import IMREAD_COLOR, imdecode, imwrite
from fastapi import HTTPException, Request
from numpy import frombuffer, uint8

from src.api.presenters import HTTPError, SuccessJSON
from src.common.enums import FileType
from src.common.params import UploadAnswerKey
from src.core.config import (
    ANSWER_KEY_FILENAME,
    IMG_DIR,
    LOG,
    WEB_DIR,
    WEB_DRIVER,
)
from src.repository.dynamic_repository import DynamicRepository
from src.utils.formaters import get_size


class AnswerKey:

    def __init__(self) -> None:
        self.__form: UploadAnswerKey = None  # type:ignore
        self.__dynamic: str = None  # type:ignore
        self.__file_path: str = None  # type:ignore
        self.__size: tuple[int, int] = None  # type:ignore

    async def save(
        self, request: Request, dynamic: str, form: UploadAnswerKey
    ) -> SuccessJSON:
        if not form.fields:
            raise HTTPException(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Missing all answer-key fields",
            )

        self.__form, self.__dynamic = form, dynamic
        dynamic_dir = IMG_DIR / dynamic
        dynamic_dir.mkdir(parents=True, exist_ok=True)
        self.__file_path = str(dynamic_dir / ANSWER_KEY_FILENAME)

        if form.web_fields:
            try:
                self.__save_from_web_fields()

            except Exception as error:  # pylint: disable=W0718
                if not form.image:
                    raise HTTPError(
                        "Error in screenshot answer-key from web files",
                        error=error,
                    ) from error

                await self.__save_from_image_field()

        elif form.image:
            await self.__save_from_image_field()

        DynamicRepository.set_size(dynamic, self.__size)
        LOG.info(f"Answer-Key image {self.__size} saved in PNG")

        return SuccessJSON(
            request,
            f"Answer key image {ANSWER_KEY_FILENAME} saved",
            {
                "dynamic": dynamic,
                "filename": ANSWER_KEY_FILENAME,
                "type": "image/png",
                "size": self.__size,
            },
        )

    def __save_from_web_fields(self) -> None:
        dynamic_dir = WEB_DIR / self.__dynamic

        if not dynamic_dir.exists():
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Dynamic {self.__dynamic} web dir not found",
            )

        html_path = dynamic_dir / FileType.HTML.file
        css_path = dynamic_dir / FileType.CSS.file

        try:
            with open(html_path, mode="w", encoding="utf-8") as file:
                file.write(self.__form.html)

            with open(css_path, mode="w", encoding="utf-8") as file:
                file.write(self.__form.css)

        except Exception as error:
            raise HTTPError(
                "Error in writing answer-key from web fields", error=error
            ) from error

        try:
            WEB_DRIVER.get(html_path.absolute().as_uri())
            WEB_DRIVER.implicitly_wait(1)
            binary_screenshot = WEB_DRIVER.get_screenshot_as_png()

        except Exception as error:
            raise HTTPError(
                f"Error in getting {self.__dynamic} answer-key screenshot",
                error=error,
            ) from error

        self.__save_image(binary_screenshot)

    async def __save_from_image_field(self) -> None:
        content_type = self.__form.image.content_type  # type:ignore
        if content_type and not content_type.startswith("image/"):
            raise HTTPException(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "Answer-key file must be an image",
            )

        try:
            content = await self.__form.image.read()  # type:ignore

        except Exception as error:  # pylint: disable=W0621
            raise HTTPError(
                f"Error in reading {self.__dynamic} answer-key screenshot",
                error=error,
            ) from error

        self.__save_image(content)

    def __save_image(self, content: bytes) -> None:
        try:
            array_screenshot = frombuffer(content, dtype=uint8)
            screenshot = imdecode(array_screenshot, IMREAD_COLOR)
            self.__size = get_size(screenshot)

            imwrite(self.__file_path, screenshot)
            LOG.info(f"{self.__dynamic} answer-key saved")

        except Exception as error:  # pylint: disable=W0621
            raise HTTPError(
                f"Error in saving {self.__dynamic} answer-key", error=error
            ) from error
