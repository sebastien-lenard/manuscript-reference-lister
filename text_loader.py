import json
import logging
from pathlib import Path
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError


class TextLoader:
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
            logging.warning(msg)

    def extract_text_from_docx(self) -> str | None:
        """Parses a .docx file and joins paragraphs with newlines."""
        if not self.file_path.is_file():
            return None
        try:
            doc = Document(self.file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except (PackageNotFoundError, BadZipFile):
            msg = f"Invalid or corrupted .docx: {self.file_path}"
            if self.raise_exception:
                raise
            logging.warning(msg)
            return None

    def load_json(self) -> dict | list | None:
        """Loads and parses JSON data."""
        if not self.file_path.is_file():
            return None
        try:
            with open(self.file_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            msg = f"Invalid JSON format: {self.file_path}"
            if self.raise_exception:
                raise
            logging.warning(msg)
            return None
