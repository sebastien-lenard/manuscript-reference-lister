import logging
import time

import httpx

# Define a logger for this module
logger = logging.getLogger(__name__)


class HTTPClientWrapper:
    def __init__(
        self,
        email: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: int = 2,
        delay: float = 1.0,
    ):
        """
        Initialize the wrapper with API politeness and retry logic parameters.
        delay: Time to wait (in seconds) before each initial request to respect API
        limits.
        """
        self.email = email
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.delay = delay
        self.client = httpx.Client(
            timeout=httpx.Timeout(self.timeout), follow_redirects=True
        )

    def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        max_retries: int | None = None,
    ) -> httpx.Response:
        """
        Performs a GET request with retry logic for network-related errors.
        Fatal errors (like 404 or malformed responses) raise immediately.
        Ensures the URL is a plain string for HTTPX compatibility
        """
        url = str(url)

        if params is None:
            params = {}
        if headers is None:
            headers = {}

        max_retries = max_retries if max_retries is not None else self.max_retries

        # Add politeness mailto if not already present
        if self.email and "mailto" not in params:
            params["mailto"] = self.email

        last_exception = None

        for attempt in range(max_retries):
            # We apply the safety delay before the actual request
            if attempt == 0 and self.delay > 0:
                time.sleep(self.delay)
            try:
                response = self.client.get(url, params=params, headers=headers)

                # If we get a 4xx or 5xx, this raises an httpx.HTTPStatusError
                response.raise_for_status()

                # Success: return the response object
                return response

            # Timeout, ConnectError, NetworkError
            except httpx.TransportError as e:
                last_exception = e
                wait_time = self.backoff_factor**attempt

                logger.warning(
                    "Network error on attempt %d/%d for URL %s. Retrying in %ds. "
                    "Error: %s",
                    attempt + 1,
                    max_retries,
                    url,
                    wait_time,
                    e,
                )

                if attempt < max_retries - 1:
                    time.sleep(wait_time)

            except httpx.HTTPStatusError as e:
                # Fatal HTTP errors (like 401, 404, 403) are not solved by retrying
                logger.error("Fatal HTTP Error for URL %s: %s", url, e)
                raise e

            except Exception as e:
                # Any other unexpected error is fatal
                logger.error("Unexpected error during request to %s: %s", url, e)
                raise e

        # If we reach here, it means all retries failed
        logger.error("All %d retries failed for URL %s", max_retries, url)
        raise last_exception

    def close(self) -> None:
        """Close the underlying HTTPX client."""
        self.client.close()
