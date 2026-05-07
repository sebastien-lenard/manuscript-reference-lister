import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TypeVar

from manuscript_reference_lister.schemas import BaseSchema
from manuscript_reference_lister.utils import (
    AppConfig,
    DataLoader,
    RequestsWrapper,
    get_config,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


class BaseRepository[T: BaseSchema]:
    """Base class for repositories that handle JSON storage."""

    def __init__(
        self,
        local_filename: str,
        model_class: type[T],
        config: AppConfig | None = None,
    ):
        self.config = config or get_config()
        self.headers = {
            "User-Agent": f"ManuscriptRefLister/1.0 (mailto:"
            f"{self.config.crossref_api_email})"
        }
        self.local_filename = local_filename
        self._load_failed = False
        self.model_class = model_class
        self.records: list[T] = []
        self.requests_wrapper = RequestsWrapper(
            self.config.crossref_api_email,
            timeout=self.config.crossref_api_timeout,
            max_retries=self.config.crossref_api_max_retry,
            delay=self.config.crossref_api_delay,
        )

    def __len__(self) -> int:
        return len(self.records)

    def deduplicate(self) -> None:
        """Removes duplicate records from the repository in-place."""
        seen = set()
        unique_records = []

        for record in self.records:
            key = record.identity_key
            if key not in seen:
                seen.add(key)
                unique_records.append(record)

        self.records = unique_records

    def load_all(
        self, input_filepath: str | Path | None = None, raise_exception=False
    ) -> None:
        """Load local records and validate against the schema. The list of records of
        the object are set to [] if invalid."""
        path = Path(
            input_filepath
            or Path(self.config.local_repo_dir_path) / self.local_filename
        )
        data = DataLoader(path, raise_exception=raise_exception).load_json()
        if data and isinstance(data, list):
            try:
                self.records = [self.model_class(**item) for item in data]
                self._load_failed = False
            except (TypeError, ValueError) as e:
                logger.warning(
                    f"Failed validation for {self.model_class.__name__} in file {path}."
                    f" Records set to [] for this run. Please check the file before a"
                    f" rerun."
                )
                if raise_exception:
                    raise e
                logger.debug(f"Error detail: {e}")
                self.records = []
                self._load_failed = True
        else:
            self.records = []
        logging.info(f"Loaded {len(self.records)} records from {str(path)}")

    def save_all(self, output_filepath: str | Path | None = None) -> None:
        """Saves records atomically using a temporary file.
        Saving is done in a recovery file if previous load_all failed."""
        protected_path = self.config.local_repo_dir_path / self.local_filename
        target_path = Path(output_filepath) if output_filepath else protected_path

        if self._load_failed and target_path == protected_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = (
                f"{target_path.stem}_recovered_{timestamp}{target_path.suffix}"
            )
            target_path = target_path.with_name(new_filename)

            # Update state so the repo "migrates" to the new file
            self.local_filename = new_filename
            self._load_failed = False
            logger.warning(
                f"Previous load failed; diverting to recovery file: {target_path}"
            )

        data_to_save = [record.to_dict() for record in self.records]
        temp_path = target_path.with_suffix(".tmp")

        try:
            # Explicitly open the file with utf-8
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            temp_path.replace(target_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()
        logging.info(f"Saved {len(self.records)} records from {str(target_path)}")
