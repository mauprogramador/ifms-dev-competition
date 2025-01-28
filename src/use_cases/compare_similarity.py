from http import HTTPStatus
from os import makedirs
from os.path import exists, join
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

        raise HTTPException(HTTPStatus.NOT_FOUND, "Answer-Key image not found")

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
