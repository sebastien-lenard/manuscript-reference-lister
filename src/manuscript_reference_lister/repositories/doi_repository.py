import logging

import requests

from manuscript_reference_lister.utils import AppConfig, RequestsWrapper, get_config


class DoiRepository:
    """Handles information specific to the DOI of a work."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or get_config()
        self.requests_wrapper = RequestsWrapper(
            self.config.crossref_api_email,
            timeout=self.config.doi_api_timeout,
            max_retries=self.config.doi_api_max_retry,
            delay=self.config.doi_api_delay,
        )

    def get_reference(self, doi: str, style: str = "apa") -> str:
        """Gets the reference formatted to a style and ready to include in a
        bibliography.
        Examples of styles:
        apa (AGU, Wiley), copernicus-publications (EGU), elsevier-harvard (Elsevier),
        chicago-author-date (Taylor & Francis), springer-basic-author-date (Springer),
        etc. Must have been validated using StyleRepository.
        Warning: doesn't handle the case when the style is not supported."""
        headers = {"Accept": f"text/x-bibliography; style={style}"}

        try:
            res = self.requests_wrapper.get(
                self.config.doi_api_url.replace("{doi}", str(doi)), headers=headers
            )  # DOI Content Negotiation Service
            res.encoding = "utf-8"
            return res.text.strip()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning("DOI not found (404): %s", doi)
                return "Reference unavailable in doi.org."
            raise e
