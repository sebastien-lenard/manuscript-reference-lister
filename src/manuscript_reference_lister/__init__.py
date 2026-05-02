from . import config_loader
from .citation_parser import CitationParser
from .data_loader import DataLoader
from .doi_repository import DoiFetcher
from .journal_parser import JournalParser
from .journal_repository import JournalFetcher
from .requests_wrapper import RequestsWrapper
from .style_repository import StyleFetcher
from .work_metadata import Work
from .work_repository import WorkFetcher

# Warning: don't include packages that can call themselves in a circular way
__all__ = [
    "config_loader",
    "CitationParser",
    "DataLoader",
    "DoiFetcher",
    "JournalFetcher",
    "JournalParser",
    "RequestsWrapper",
    "StyleFetcher",
    "Work",
    "WorkFetcher",
]
