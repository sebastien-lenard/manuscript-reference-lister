from unittest.mock import MagicMock, patch

import pytest
import requests

from manuscript_reference_lister.repositories import DoiRepository


@pytest.fixture
def repo() -> DoiRepository:
    """Provides a fresh instance of DoiRepository for each test."""
    return DoiRepository()


def test_get_reference_success(repo: DoiRepository) -> None:
    """Verify formatted reference is returned correctly with proper headers."""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Doe, J. (2023). Title of the Paper. Journal of Science."

    with patch.object(
        repo.http_client_wrapper, "get", return_value=mock_response
    ) as mock_get:
        doi = "10.1000/182"
        style = "apa"
        result = repo.get_reference(doi, style)

        assert result == "Doe, J. (2023). Title of the Paper. Journal of Science."

        _, kwargs = mock_get.call_args
        assert "headers" in kwargs
        assert kwargs["headers"]["Accept"] == f"text/x-bibliography; style={style}"


def test_get_reference_not_found(repo: DoiRepository) -> None:
    """Verify fallback string is returned when a 404 error occurs."""

    mock_response = MagicMock(status_code=404)
    error = requests.exceptions.HTTPError("404 Client Error", response=mock_response)

    with patch.object(repo.http_client_wrapper, "get", side_effect=error):
        result = repo.get_reference("invalid/doi", "apa")
        assert result == "Reference unavailable in doi.org."


def test_get_reference_utf8_encoding(repo: DoiRepository) -> None:
    """Verify that special characters (accented, dashes) are handled correctly."""
    # This string contains 'é' and an em-dash '—'
    utf8_text = "Lavé, J. (2020). Steady erosion — Himalayas."

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = utf8_text

    with patch.object(repo.http_client_wrapper, "get", return_value=mock_response):
        result = repo.get_reference("10.1038/s41561-020-0585-2", "apa")

        assert result == utf8_text
        # Ensure the repo actually tried to set the encoding to utf-8
        assert mock_response.encoding == "utf-8"
