from dataclasses import dataclass, field
from datetime import date
from typing import override

from .base_schema import BaseSchema


@dataclass
class JournalMetadata(BaseSchema):
    """Represents validated metadata for a scientific journal."""

    input_title: str  # e.g. Nature Geoscience
    true_title: str | None = None  # e.g. Nature Geoscience
    publisher: str | None = None  # e.g. Nature Portfolio / Springer Nature
    ISSN: str | None = None  # e.g. 1752-0894
    start_year: int | None = None  # e.g. 2008
    end_year: int | None = None  # e.g. 2026
    update: str = field(
        default_factory=lambda: str(date.today())
    )  # ISO format: YYYY-MM-DD

    @override
    @property
    def identity_key(self) -> tuple[str, str]:
        """Returns the unique identifier used for deduplication."""
        return (self.input_title, self.ISSN)
