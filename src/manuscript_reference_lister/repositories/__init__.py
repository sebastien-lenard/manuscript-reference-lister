from .base_repository import BaseRepository
from .doi_repository import DoiRepository
from .journal_repository import JournalRepository
from .style_repository import StyleRepository
from .work_repository import WorkRepository

# Warning: don't include packages that can call themselves in a circular way
__all__ = [
    "BaseRepository",
    "DoiRepository",
    "JournalRepository",
    "StyleRepository",
    "WorkRepository",
]
