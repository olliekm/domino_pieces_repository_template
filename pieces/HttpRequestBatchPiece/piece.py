from domino.base_piece import BasePiece
from .models import InputModel, OutputModel
from concurrent.futures import ThreadPoolExecutor
import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DominoHttpRequestBatchPiece/1.0)"
}


def _fetch_one(url: str, results_path: str, idx: int) -> str:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    file_path = f"{results_path}/fetched_{idx}"
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path


class HttpRequestBatchPiece(BasePiece):

    def piece_function(self, input_data: InputModel):

        self.logger.info(f"Fetching {len(input_data.urls)} URLs")

        max_workers = min(input_data.max_workers, len(input_data.urls)) or 1
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(
                lambda args: _fetch_one(*args),
                [(url, self.results_path, idx) for idx, url in enumerate(input_data.urls)]
            ))

        return OutputModel(file_paths=results)
