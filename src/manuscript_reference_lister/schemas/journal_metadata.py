from datetime import date
from typing import Self

from pydantic import Field, field_validator, model_validator

from .base_schema import BaseSchema


class JournalMetadata(BaseSchema):
    """Represents validated metadata for a scientific journal."""

    input_title: str  # e.g. Nature Geoscience
    true_title: str | None = None  # e.g. Nature Geoscience
    publisher: str | None = None  # e.g. Nature Portfolio / Springer Nature
    ISSN: str | None = None  # e.g. 1752-0894
    start_year: int | None = Field(default=None, ge=1600, le=2099)  # e.g. 2008
    end_year: int | None = Field(default=None, ge=1600, le=2099)  # e.g. 2026
    update: str = Field(
        default_factory=lambda: str(date.today())
    )  # ISO format: YYYY-MM-DD

    @property
    def identity_key(self) -> tuple[str, str | None]:
        """Returns the unique identifier used for deduplication."""
        return (self.input_title, self.ISSN)

    @field_validator("ISSN")
    @classmethod
    def validate_issn_format(cls, v: str | None) -> str | None:
        """Validate ISSN."""
        if v and len(v) == 8 and "-" not in v:
            return f"{v[:4]}-{v[4:]}"
        return v

    @model_validator(mode="after")
    def validate_year_range(self) -> Self:
        """Validate years."""
        if self.start_year and self.end_year:
            if self.start_year > self.end_year:
                raise ValueError(
                    f"start_year ({self.start_year}) should be lower than end_year"
                    f" ({self.end_year})"
                )
        return self
