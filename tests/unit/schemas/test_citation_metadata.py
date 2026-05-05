from manuscript_reference_lister.schemas.citation_metadata import CitationMetadata


def test_citation_metadata_instantiation():
    """Verify that CitationMetadata creates an object with expected defaults."""
    citation = CitationMetadata(
        first_authors_txt="Lenard et al.", year_and_suffix="2020a"
    )

    assert citation.first_authors_txt == "Lenard et al."
    assert citation.year_and_suffix == "2020a"
    assert citation.type == "narrative"


def test_citation_metadata_identity_key():
    """Verify the deduplication key is correctly formed."""
    citation = CitationMetadata(
        first_authors_txt="Guns and Vanacker",
        year_and_suffix="2021",
        type="parenthetical",
    )

    expected_key = ("Guns and Vanacker", "2021")
    assert citation.identity_key == expected_key
