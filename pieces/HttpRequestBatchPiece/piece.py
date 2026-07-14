from domino.base_piece import BasePiece
from .models import InputModel, OutputModel
from concurrent.futures import ThreadPoolExecutor
import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DominoHttpRequestBatchPiece/1.0)"
}


def _fetch_one(url: str, results_path: str, idx: int) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        return None, url, str(e)

    file_path = f"{results_path}/fetched_{idx}"
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path, url, None


class HttpRequestBatchPiece(BasePiece):

    def piece_function(self, input_data: InputModel):

        self.logger.info(f"Fetching {len(input_data.urls)} URLs")

        max_workers = min(input_data.max_workers, len(input_data.urls)) or 1
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            fetch_results = list(pool.map(
                lambda args: _fetch_one(*args),
                [(url, self.results_path, idx) for idx, url in enumerate(input_data.urls)]
            ))

        file_paths = []
        failures = []
        for file_path, url, error in fetch_results:
            if file_path is not None:
                file_paths.append(file_path)
            else:
                failures.append((url, error))

        for url, error in failures:
            self.logger.error(f"Failed to fetch {url}: {error}")

        self.logger.info(f"Fetched {len(file_paths)}/{len(input_data.urls)} URLs successfully")

        return OutputModel(file_paths=file_paths)
