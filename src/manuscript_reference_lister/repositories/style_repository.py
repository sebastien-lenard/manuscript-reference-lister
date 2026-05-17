import logging

from manuscript_reference_lister.network import (
    HTTPClientWrapper,
    get_http_client_registry,
)
from manuscript_reference_lister.utils import AppConfig, get_config

logger = logging.getLogger(__name__)


class StyleRepository:
    """Handles information about reference styles."""

    def __init__(
        self,
        favored_style: str = "apa",
        config: AppConfig | None = None,
        registry: HTTPClientWrapper | None = None,
    ):
        """Examples of styles:
        apa (AGU, Wiley), copernicus-publications (EGU), elsevier-harvard (Elsevier),
        chicago-author-date (Taylor & Francis), springer-basic-author-date (Springer),
        etc.
        """
        self.config = config or get_config()
        registry = registry or get_http_client_registry()
        self.http_client_wrapper = registry.get_client("crossref")
        self.headers = {
            "User-Agent": f"ManuscriptRefLister/1.0 "
            f"(mailto:{self.config.crossref_api_email})"
        }
        self.favored_style = favored_style
        self.favored_style_is_valid = None

    def validate_favored_style(self) -> None:
        """Check if the favored reference style is in the repository and supported."""
        response = self.http_client_wrapper.get(
            self.config.crossref_api_styles_url, headers=self.headers
        )
        valid_styles = response.json()["message"]["items"]
        if self.favored_style in valid_styles:
            self.favored_style_is_valid = True
            logger.info(
                "Favored reference style validated successfully: %s",
                self.favored_style,
                extra={
                    "status": "OK",
                    "event": "style_validation_success",
                    "style": self.favored_style,
                },
            )
        else:
            self.favored_style_is_valid = False
            logger.warning(
                "Favored reference style invalid: %s",
                self.favored_style,
                extra={
                    "status": "KO",
                    "event": "style_validation_failed",
                    "style": self.favored_style,
                },
            )
