from typing import TypedDict


class JournalMetadata(TypedDict):
    input_title: str  # e.g. Nature Geoscience
    true_title: str  # e.g. Nature Geoscience
    publisher: str  # e.g. Nature Portfolio / Springer Nature
    ISSN: str  # e.g. 1752-0894
    start_year: int  # e.g. 2008
    end_year: int  # e.g. 2026
    update: str  # e.g. 2026-03-27
