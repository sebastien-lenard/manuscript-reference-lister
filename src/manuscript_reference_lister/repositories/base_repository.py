import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from manuscript_reference_lister.utils import (
    AppConfig,
    DataLoader,
    RequestsWrapper,
    get_config,
)

T = TypeVar("T")


class BaseRepository[T]:
    """Base class for repositories that handle JSON storage."""

    def __init__(
        self,
        local_filename: str,
        validator: Callable[[Any], bool],
        config: AppConfig | None = None,
    ):
        self.config = config or get_config()
        self.headers = {
            "User-Agent": f"ManuscriptRefLister/1.0 (mailto:"
            f"{self.config.crossref_api_email})"
        }
        self.local_filename = local_filename
        self.validator = validator
        self.records: list[T] = []
        self.requests_wrapper = RequestsWrapper(
            self.config.crossref_api_email,
            timeout=self.config.crossref_api_timeout,
            max_retries=self.config.crossref_api_max_retry,
            delay=self.config.crossref_api_delay,
        )

    def __len__(self) -> int:
        return len(self.records)

    def load_all(self, input_filepath: str | Path | None = None) -> None:
        """Load local records and validate against the schema."""
        path = Path(
            input_filepath
            or Path(self.config.local_repo_dir_path) / self.local_filename
        )
        data = DataLoader(path, raise_exception=False).load_json(self.validator)
        self.records = data if data is not None else []

    def save_all(self, output_filepath: str | Path | None = None) -> None:
        """Saves records atomically using temporary files."""
        output_filepath = Path(
            output_filepath
            or Path(self.config.local_repo_dir_path) / self.local_filename
        )

        json_data = json.dumps(self.records, indent=4, ensure_ascii=False)
        temp_path = output_filepath.with_suffix(".tmp")

        try:
            temp_path.write_text(json_data, encoding="utf-8")
            temp_path.replace(output_filepath)
        finally:
            if temp_path.exists():
                temp_path.unlink()
