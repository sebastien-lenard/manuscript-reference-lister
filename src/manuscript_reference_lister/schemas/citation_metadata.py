from typing import Literal, override

from pydantic import Field

from .base_schema import BaseSchema


class CitationMetadata(BaseSchema):
    """Represents validated metadata for a citation in a manuscript."""

    model_config = {"frozen": True}

    first_authors_txt: str = Field(
        min_length=1
    )  # e.g. Lenard et al., Guns and Vanacker
    year_and_suffix: str = Field(pattern=r"^\d{4}[a-z]?$")  # e.g. 2020a
    type: Literal["narrative", "parenthetical"] = "narrative"

    @override
    @property
    def identity_key(self) -> tuple[str, str]:
        """Returns the unique identifier used for deduplication."""
        return (self.first_authors_txt, self.year_and_suffix)
