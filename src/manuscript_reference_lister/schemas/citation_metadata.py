from dataclasses import dataclass
from typing import Literal, override

from .base_schema import BaseSchema


@dataclass
class CitationMetadata(BaseSchema):
    """Represents validated metadata for a citation in a manuscript."""

    first_authors_txt: str  # e.g. Lenard et al., Guns and Vanacker
    year_and_suffix: str  # e.g. 2020a
    type: Literal["narrative", "parenthetical"] = "narrative"

    @override
    @property
    def identity_key(self) -> tuple[str, str]:
        """Returns the unique identifier used for deduplication."""
        return (self.first_authors_txt, self.year_and_suffix)
