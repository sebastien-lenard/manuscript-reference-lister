from dataclasses import dataclass
from typing import override

from .base_schema import BaseSchema

# TODO: maybe some fields need to be None when they are ""


@dataclass
class WorkMetadata(BaseSchema):
    """Represents validated metadata for a published work."""

    input_first_authors_txt: str  # e.g. Lenard et al., Guns and Vanacker
    input_year_and_suffix: str  # e.g. 2020a
    input_ISSN: str  # e.g. 1752-0894
    reference: str | None = (
        None  # e.g. Lenard, S. J. P., Lavé, J., France-Lanord, C., Aumaître, G., Bourlès, D. L., & Keddadouche, K. (2020). Steady erosion rates in the Himalayas through late Cenozoic climatic changes. Nature Geoscience, 13(6), 448–452. https://doi.org/10.1038/s41561-020-0585-2
    )
    style: str | None = None  # e.g. apa
    DOI: str | None = None  # e.g. 10.1038/s41561-020-0585-2
    type: str | None = None  # e.g. journal-article

    @override
    @property
    def identity_key(self) -> tuple[str, str, str, str | None]:
        """Returns the unique identifier used for deduplication."""
        return (
            self.input_first_authors_txt,
            self.input_year_and_suffix,
            self.input_ISSN,
            self.DOI,
        )
