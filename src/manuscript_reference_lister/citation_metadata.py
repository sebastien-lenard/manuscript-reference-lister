from typing import Literal, TypedDict


class CitationMetadata(TypedDict):
    first_authors: str
    year_and_suffix: str
    type: Literal["narrative", "parenthetical"]
