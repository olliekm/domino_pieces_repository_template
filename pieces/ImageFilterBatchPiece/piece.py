from domino.base_piece import BasePiece
from .models import InputModel, OutputModel, ImageResult
from pathlib import Path
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import base64
import os


filter_masks = {
    'sepia': ((0.393, 0.769, 0.189), (0.349, 0.686, 0.168), (0.272, 0.534, 0.131)),
    'black_and_white': ((0.333, 0.333, 0.333), (0.333, 0.333, 0.333), (0.333, 0.333, 0.333)),
    'brightness': ((1.4, 0, 0), (0, 1.4, 0), (0, 0, 1.4)),
    'darkness': ((0.6, 0, 0), (0, 0.6, 0), (0, 0, 0.6)),
    'contrast': ((1.2, 0.6, 0.6), (0.6, 1.2, 0.6), (0.6, 0.6, 1.2)),
    'red': ((1.6, 0, 0), (0, 1, 0), (0, 0, 1)),
    'green': ((1, 0, 0), (0, 1.6, 0), (0, 0, 1)),
    'blue': ((1, 0, 0), (0, 1, 0), (0, 0, 1.6)),
    'cool': ((0.9, 0, 0), (0, 1.1, 0), (0, 0, 1.3)),
    'warm': ((1.2, 0, 0), (0, 0.9, 0), (0, 0, 0.8)),
}


def _load_image(image_input: str) -> Image.Image:
    max_path_size = int(os.pathconf('/', 'PC_PATH_MAX'))
    if len(image_input) < max_path_size and Path(image_input).exists() and Path(image_input).is_file():
        return Image.open(image_input)

    try:
        decoded_data = base64.b64decode(image_input)
        image_stream = BytesIO(decoded_data)
        image = Image.open(image_stream)
        image.verify()
        image = Image.open(image_stream)
        return image
    except Exception:
        raise ValueError("Input image is not a file path or a base64 encoded string")


def _apply_filters(np_image: np.ndarray, all_filters: list) -> np.ndarray:
    for filter_name in all_filters:
        np_mask = np.array(filter_masks[filter_name], dtype=float)
        rgb = np_image[..., :3]
        np_image[..., :3] = rgb @ np_mask.T
        np_image = np.clip(np_image, 0, 255)
    return np_image


def _process_one(image_input: str, all_filters: list, output_type: str, results_path: str, idx: int) -> ImageResult:
    image = _load_image(image_input)

    np_image = np.array(image, dtype=float)
    np_image = _apply_filters(np_image, all_filters)

    np_image = np_image.astype(np.uint8)
    modified_image = Image.fromarray(np_image)

    image_file_path = ""
    if output_type == "file" or output_type == "both":
        image_file_path = f"{results_path}/modified_image_{idx}.png"
        modified_image.save(image_file_path)

    image_base64_string = ""
    if output_type == "base64_string" or output_type == "both":
        buffered = BytesIO()
        modified_image.save(buffered, format="PNG")
        image_base64_string = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return ImageResult(
        image_base64_string=image_base64_string,
        image_file_path=image_file_path,
    )


class ImageFilterBatchPiece(BasePiece):

    def piece_function(self, input_data: InputModel):

        all_filters = list()
        if input_data.sepia:
            all_filters.append('sepia')
        if input_data.black_and_white:
            all_filters.append('black_and_white')
        if input_data.brightness:
            all_filters.append('brightness')
        if input_data.darkness:
            all_filters.append('darkness')
        if input_data.contrast:
            all_filters.append('contrast')
        if input_data.red:
            all_filters.append('red')
        if input_data.green:
            all_filters.append('green')
        if input_data.blue:
            all_filters.append('blue')
        if input_data.cool:
            all_filters.append('cool')
        if input_data.warm:
            all_filters.append('warm')

        self.logger.info(f"Applying filters: {', '.join(all_filters)}")
        self.logger.info(f"Processing {len(input_data.input_images)} images")

        max_workers = min(input_data.max_workers, len(input_data.input_images)) or 1
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(
                lambda args: _process_one(*args),
                [
                    (img, all_filters, input_data.output_type, self.results_path, idx)
                    for idx, img in enumerate(input_data.input_images)
                ]
            ))

        first_result = results[0]
        self.display_result = {
            "file_type": "png",
            "file_path": first_result.image_file_path,
        }
        if first_result.image_base64_string:
            self.display_result["base64_content"] = first_result.image_base64_string

        return OutputModel(images=results)
