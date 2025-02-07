from http import HTTPStatus
from pathlib import Path

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
from cv2.typing import MatLike
from fastapi import HTTPException
from numpy import all as np_all
from numpy import count_nonzero, frombuffer, full_like
from numpy import sum as np_sum
from numpy import uint8

from src.api.presenters import HTTPError
from src.common.enums import FileType
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
from src.utils.formaters import get_size


class Similarity:

    def __init__(self) -> None:
        self.__dynamic: str = None
        self.__code: str = None
        self.__info: str = None

    async def compare(
        self,
        dynamic: str,
        code: str,
    ) -> float:
        self.__dynamic, self.__code = dynamic, code
        self.__info = f"{dynamic} {code}"
        html_path = WEB_DIR / dynamic / code / FileType.HTML.file

        if not html_path.exists():
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f"Index.html not found in {dynamic} {code} code dir",
            )

        screenshot = self.__take_screenshot(html_path)

        size = DynamicRepository.get_size(dynamic)
        LOG.debug({"answer_key_size": size})

        answer_key_path = IMG_DIR / dynamic / ANSWER_KEY_FILENAME

        if not answer_key_path.exists():
            LOG.error("Answer-key image not found")

            raise HTTPException(
                HTTPStatus.NOT_FOUND, "Answer-key image not found"
            )

        try:
            answer_key = imread(str(answer_key_path))
            LOG.debug(
                {
                    "answer_key_shape": answer_key.shape,
                    "screenshot_shape": screenshot.shape,
                }
            )

            screenshot = self.__save_and_resize_screenshot(
                answer_key.shape, screenshot, size
            )

            total_pixels = answer_key.shape[0] * answer_key.shape[1]
            diff = absdiff(answer_key, screenshot)

            num_diff_pixels = count_nonzero(np_sum(diff, 2))
            percentage_diff: float = (num_diff_pixels / total_pixels) * 100
            similarity = 100.00 - percentage_diff

            LOG.debug(
                {
                    "total_pixels": total_pixels,
                    "num_diff_pixels": num_diff_pixels,
                }
            )

            self.__save_diff_image(answer_key, screenshot)

        except Exception as error:
            raise HTTPError(
                f"Error in handling {dynamic} {code} images to compare",
                error=error,
            ) from error

        LOG.info(f"Similarity of {code} to the answer-key: {similarity:.2f}%")

        return similarity

    def __take_screenshot(self, html_path: Path) -> MatLike:
        try:
            WEB_DRIVER.get(html_path.absolute().as_uri())
            WEB_DRIVER.implicitly_wait(1)
            binary_screenshot = WEB_DRIVER.get_screenshot_as_png()

        except Exception as error:
            raise HTTPError(
                f"Error in getting {self.__info} screenshot",
                error=error,
            ) from error

        try:
            array_screenshot = frombuffer(binary_screenshot, dtype=uint8)
            screenshot = imdecode(array_screenshot, IMREAD_COLOR)

        except Exception as error:
            raise HTTPError(
                f"Error in decode {self.__info} screenshot",
                error=error,
            ) from error

        return screenshot

    def __save_and_resize_screenshot(
        self,
        answer_key_shape: tuple[int, int, int],
        screenshot: MatLike,
        size: tuple[int, int],
    ) -> MatLike:
        if answer_key_shape != screenshot.shape:
            LOG.error("Answer-key and screenshot have different sizes")
            old_size = get_size(screenshot)
            LOG.info(f"Resizing screenshot from {old_size} to {size}")

            try:
                screenshot = resize(
                    screenshot,
                    size,
                    interpolation=INTER_CUBIC,
                )

            except Exception as error:
                raise HTTPError(
                    f"Error in resizing {self.__info} screenshot",
                    error=error,
                ) from error

        img_dir = IMG_DIR / self.__dynamic / self.__code
        img_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = img_dir / SCREENSHOT_FILENAME

        imwrite(str(screenshot_path), screenshot)
        LOG.info(f"{self.__info} screenshot saved")

        return screenshot

    def __save_diff_image(
        self, answer_key: MatLike, screenshot: MatLike
    ) -> None:
        try:
            diff = subtract(answer_key, screenshot)
            gray_diff = cvtColor(diff, COLOR_BGR2GRAY)

            diff = threshold(gray_diff, 30, 255, THRESH_BINARY)[1]
            diff = cvtColor(diff, COLOR_GRAY2BGR)
            diff[:, :, 0] = 0
            diff[:, :, 1] = 0

            black_pixels_mask = np_all(diff == 0, axis=2)
            white_image = full_like(answer_key, 255)
            diff[black_pixels_mask] = white_image[black_pixels_mask]

            diff_path = IMG_DIR / self.__dynamic / self.__code / DIFF_FILENAME
            imwrite(str(diff_path), diff)

        except Exception as error:
            raise HTTPError(
                f"Error in getting {self.__info} diff image",
                error=error,
            ) from error
