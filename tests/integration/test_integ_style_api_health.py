import pytest

from manuscript_reference_lister.repositories import StyleRepository


@pytest.mark.integration
@pytest.mark.vcr
def test_style_api_health() -> None:
    """Check Crossref Style API health and verify Polite Pool headers via VCR."""

    repo = StyleRepository("apa")
    headers = {
        "User-Agent": f"ManuscriptRefLister/1.0 (mailto:"
        f"{repo.config.crossref_api_email})"
    }

    repo.validate_favored_style()
    assert repo.favored_style_is_valid is True, (
        "APA style was not found or API call failed."
    )

    response = repo.http_client_wrapper.get(
        repo.config.crossref_api_styles_url, headers=headers
    )

    limit = response.headers.get("X-Rate-Limit-Limit")
    assert limit is not None, "X-Rate-Limit-Limit header is missing from the response."
