from domino.base_piece import BasePiece
from .models import InputModel, OutputModel
from concurrent.futures import ThreadPoolExecutor
import requests
import base64


def _fetch_one(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return base64.b64encode(response.content).decode('utf-8')


class HttpRequestBatchPiece(BasePiece):

    def piece_function(self, input_data: InputModel):

        self.logger.info(f"Fetching {len(input_data.urls)} URLs")

        max_workers = min(input_data.max_workers, len(input_data.urls)) or 1
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(_fetch_one, input_data.urls))

        return OutputModel(base64_bytes_data_list=results)
