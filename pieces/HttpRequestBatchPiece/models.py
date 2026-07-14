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
    file_paths: List[str] = Field(
        default_factory=list,
        description='List of file paths where the fetched content was saved, in the same order as the input URLs.',
    )
