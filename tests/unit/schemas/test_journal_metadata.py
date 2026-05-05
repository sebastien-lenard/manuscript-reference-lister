from datetime import date

from manuscript_reference_lister.schemas import JournalMetadata


def test_journal_metadata_defaults():
    """Ensure optional fields default to None and date is today."""
    journal = JournalMetadata(input_title="Science")
    assert journal.ISSN is None
    assert journal.update == str(date.today())


def test_journal_metadata_identity_key():
    """Ensure deduplication key is composed correctly."""
    journal = JournalMetadata(input_title="Nature", ISSN="1234-5678")
    assert journal.identity_key == ("Nature", "1234-5678")
