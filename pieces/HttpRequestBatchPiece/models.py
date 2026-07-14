from pydantic import BaseModel, Field
from typing import List


class InputModel(BaseModel):
    urls: List[str] = Field(
        description='List of URLs to fetch via GET request.',
        json_schema_extra={
            "from_upstream": "allowed"
        }
    )
    max_workers: int = Field(
        default=5,
        description='Maximum number of URLs to fetch concurrently.',
    )


class OutputModel(BaseModel):
    base64_bytes_data_list: List[str] = Field(
        default_factory=list,
        description='List of base64 encoded response bodies, in the same order as the input URLs.',
    )
