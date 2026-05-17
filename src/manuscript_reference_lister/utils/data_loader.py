import json
import logging
from pathlib import Path
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles data loading and text extraction for DOCX and JSON files.

    Attributes:
        file_path: Path to the source file.
        raise_exception: If True, invalid files trigger errors;
            otherwise, logs a warning.
    """

    def __init__(self, file_path: str | Path, raise_exception: bool = True):
        self.file_path = Path(file_path)
        self.raise_exception = raise_exception
        if not self.file_path.is_file():
            msg = f"Input file not found: {self.file_path}"
            if self.raise_exception:
                raise FileNotFoundError(msg)
            logger.warning(
                "Input file not found: %s",
                self.file_path,
                extra={
                    "status": "KO",
                    "event": "file_not_found",
                    "filepath": str(self.file_path),
                },
            )

    def extract_text_from_docx(self) -> str | None:
        """Parses a .docx file and joins paragraphs with newlines."""
        if not self.file_path.is_file():
            return None
        try:
            doc = Document(self.file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except (PackageNotFoundError, BadZipFile):
            if self.raise_exception:
                raise
            logger.warning(
                "Invalid or corrupted .docx: %s",
                self.file_path,
                extra={
                    "status": "KO",
                    "event": "docx_corruption_detected",
                    "filepath": str(self.file_path),
                },
            )
            return None

    def load_json(self, validator=None) -> dict | list | None:
        """Loads and parses JSON data. Returns None if file corrupted and if a list not
        records not validated by the validator function."""
        if not self.file_path.is_file():
            return None
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if self.raise_exception:
                raise
            logger.warning(
                "Invalid JSON format: %s",
                self.file_path,
                extra={
                    "status": "KO",
                    "event": "json_decode_error",
                    "filepath": str(self.file_path),
                },
            )
            return None

        if data is None:
            return None

        if validator and isinstance(data, list):
            if not all(validator(item) for item in data):
                msg = (
                    f"Schema validation failed for one or more items in: "
                    f"{self.file_path}"
                )
                if self.raise_exception:
                    raise ValueError(msg)
                logger.warning(
                    "Schema validation failed for item in: %s",
                    self.file_path,
                    extra={
                        "status": "KO",
                        "event": "json_schema_validation_failed",
                        "filepath": str(self.file_path),
                    },
                )
                return None

        return data
