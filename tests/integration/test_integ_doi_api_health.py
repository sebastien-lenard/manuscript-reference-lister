import pytest

from manuscript_reference_lister.repositories import DoiRepository


@pytest.mark.integration
@pytest.mark.vcr  # Activate interception and automated creation of YAML cassette
def test_doi_api_service_health() -> None:
    """Check DOI Content Negotiation Service health and verify caching via VCR."""
    repo = DoiRepository()

    # DOI Steady erosion rates in the Himalayas through late Cenozoic climatic changes
    test_doi = "10.1038/s41561-020-0585-2"
    test_style = "apa"

    reference = repo.get_reference(test_doi, test_style)

    assert reference != "Reference unavailable in doi.org.", (
        "DOI service returned 'unavailable' message."
    )
    assert len(reference) > 10, "The returned reference is suspiciously too short."

    assert "Nature Geoscience" in reference, (
        "Citation content did not contain expected publisher name."
    )
