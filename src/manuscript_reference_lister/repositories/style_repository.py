import logging

from manuscript_reference_lister.utils import AppConfig, RequestsWrapper, get_config


class StyleRepository:
    """Handles information about reference styles."""

    def __init__(self, favored_style: str = "apa", config: AppConfig | None = None):
        """
        Examples of styles:
        apa (AGU, Wiley), copernicus-publications (EGU), elsevier-harvard (Elsevier),
        chicago-author-date (Taylor & Francis), springer-basic-author-date (Springer),
        etc.
        """
        self.config = config or get_config()
        self.headers = {
            "User-Agent": f"ManuscriptRefLister/1.0 "
            f"(mailto:{self.config.crossref_api_email})"
        }
        self.favored_style = favored_style
        self.favored_style_is_valid = None
        self.requests_wrapper = RequestsWrapper(
            self.config.crossref_api_email,
            timeout=self.config.crossref_api_timeout,
            max_retries=self.config.crossref_api_max_retry,
            delay=self.config.crossref_api_delay,
        )

    def validate_favored_style(self) -> None:
        """Check is the favored reference style is in the repository and supported."""
        response = self.requests_wrapper.get(
            self.config.crossref_api_styles_url, headers=self.headers
        )
        valid_styles = response.json()["message"]["items"]
        if self.favored_style in valid_styles:
            self.favored_style_is_valid = True
        else:
            self.favored_style_is_valid = False
            logging.warning("Invalid style %s.", self.favored_style)
