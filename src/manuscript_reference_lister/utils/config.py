import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    # Directories
    local_repo_dir_path: Path
    output_dir_path: Path

    # Crossref API
    crossref_api_delay: float
    crossref_api_email: str
    crossref_api_journals_url: str
    crossref_api_journals_issn_url: str
    crossref_api_styles_url: str
    crossref_api_works_url: str
    crossref_api_works_get_limit: int
    crossref_api_timeout: float
    crossref_api_max_retry: int

    # DOI Service
    doi_api_delay: float
    doi_api_url: str
    doi_api_timeout: float
    doi_api_max_retry: int

    # Other Logic
    context_keywords: str
    journal_update_days: int
    journal_update_limit: int

    # Blacklist
    parser_blacklist: list[str] = field(
        default_factory=lambda: [
            "Fig",
            "Figs",
            "Figure",
            "Figures",
            "Tab",
            "Table",
            "Eq",
            "Plate",
            "Section",
            "See",
            "e.g.",
            "i.e.",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
    )

    def ensure_directories(self):
        """Ensures that the local repository and output directories exist."""
        for d in [self.local_repo_dir_path, self.output_dir_path]:
            d.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    """Factory function to load .env and create the config object."""
    load_dotenv()

    config = AppConfig(
        local_repo_dir_path=Path(os.getenv("LOCAL_REPO_DIR_PATH", "repo")),
        output_dir_path=Path(os.getenv("OUTPUT_DIR_PATH", "output")),
        crossref_api_delay=float(os.getenv("CROSSREF_API_DELAY", 0.5)),
        crossref_api_email=os.getenv("CROSSREF_API_EMAIL", "default@example.com"),
        crossref_api_journals_url=os.getenv("CROSSREF_API_JOURNALS_URL", ""),
        crossref_api_journals_issn_url=os.getenv("CROSSREF_API_JOURNALS_ISSN_URL", ""),
        crossref_api_styles_url=os.getenv("CROSSREF_API_STYLES_URL", ""),
        crossref_api_works_url=os.getenv("CROSSREF_API_WORKS_URL", ""),
        crossref_api_works_get_limit=int(os.getenv("CROSSREF_API_WORKS_GET_LIMIT", 6)),
        crossref_api_timeout=float(os.getenv("CROSSREF_API_TIMEOUT", 10)),
        crossref_api_max_retry=int(os.getenv("CROSSREF_API_MAX_RETRY", 10)),
        doi_api_delay=float(os.getenv("DOI_API_DELAY", 0.4)),
        doi_api_url=os.getenv("DOI_API_URL", ""),
        doi_api_timeout=float(os.getenv("DOI_API_TIMEOUT", 10)),
        doi_api_max_retry=int(os.getenv("DOI_API_MAX_RETRY", 10)),
        context_keywords=os.getenv("CONTEXT_KEYWORDS", ""),
        journal_update_days=int(os.getenv("JOURNAL_UPDATE_DAYS", 30)),
        journal_update_limit=int(os.getenv("JOURNAL_UPDATE_LIMIT", 100)),
    )

    # Call directory creation once loaded
    config.ensure_directories()
    return config


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Gets current cached config or load it."""
    config = load_config()
    return config
