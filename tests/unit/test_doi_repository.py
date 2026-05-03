from unittest.mock import MagicMock, patch

import pytest
import requests

from manuscript_reference_lister import DoiRepository


@pytest.fixture
def repo() -> DoiRepository:
    """Provides a fresh instance of DoiRepository for each test."""
    return DoiRepository()


@patch("manuscript_reference_lister.doi_repository.RequestsWrapper.get")
def test_get_reference_success(
    mock_wrapper_get: MagicMock, repo: DoiRepository
) -> None:
    """Verify formatted reference is returned correctly with proper headers."""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Doe, J. (2023). Title of the Paper. Journal of Science."
    mock_wrapper_get.return_value = mock_response

    doi = "10.1000/182"
    style = "apa"
    result = repo.get_reference(doi, style)

    assert result == "Doe, J. (2023). Title of the Paper. Journal of Science."

    _, kwargs = mock_wrapper_get.call_args
    assert "headers" in kwargs
    assert kwargs["headers"]["Accept"] == f"text/x-bibliography; style={style}"


@patch("manuscript_reference_lister.doi_repository.RequestsWrapper.get")
def test_get_reference_not_found(
    mock_wrapper_get: MagicMock, repo: DoiRepository
) -> None:
    """Verify fallback string is returned when a 404 error occurs."""

    mock_response = MagicMock(status_code=404)
    error = requests.exceptions.HTTPError("404 Client Error", response=mock_response)
    mock_wrapper_get.side_effect = error

    result = repo.get_reference("invalid/doi", "apa")

    assert result == "Reference unavailable in doi.org."
