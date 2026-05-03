import json
import logging
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from manuscript_reference_lister import JournalRepository


@pytest.fixture
def repo(tmp_path: Path) -> JournalRepository:
    """Provides a fresh instance of JournalRepository for each test."""
    repo = JournalRepository()
    repo.work_dir_path = str(tmp_path)
    return repo


def test_get_journal_metadata_success(repo: JournalRepository) -> None:
    """Verify successful retrieval of ISSNs and years from multiple API endpoints."""
    # 1. Main search response
    mock_main = MagicMock(status_code=200)
    mock_main.json.return_value = {
        "message": {"items": [{"title": "Geology", "ISSN": ["0091-7613"]}]}
    }

    # 2. Year endpoint response (reused for min/max)
    mock_year = MagicMock(status_code=200)
    mock_year.json.return_value = {
        "message": {
            "items": [
                {
                    "published-print": {"date-parts": [[1973]]},
                    "published-online": {"date-parts": [[1995]]},
                }
            ]
        }
    }

    with patch(
        "manuscript_reference_lister.journal_repository.RequestsWrapper.get"
    ) as mock_get:
        mock_get.side_effect = [mock_main, mock_year, mock_year]

        results = repo.get_journal_metadata("Geology")

        assert len(results) == 1
        assert results[0]["issn"] == "0091-7613"
        assert results[0]["start_year"] == 1973
        assert results[0]["end_year"] == 1995


def test_get_journal_metadata_not_found_behavior(
    repo: JournalRepository, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify fallback to template and warning log when no journal is found."""
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"message": {"items": []}}

    with patch(
        "manuscript_reference_lister.journal_repository.RequestsWrapper.get",
        return_value=mock_resp,
    ):
        with caplog.at_level(logging.WARNING):
            results = repo.get_journal_metadata("Unknown Journal")

            assert any(
                "Unknown Journal not found" in record.message
                for record in caplog.records
            )
            assert len(results) == 1
            assert results[0]["issn"] is None
            assert results[0]["input_title"] == "Unknown Journal"


# TODO: Lacks a unit test for test_get_issn_year_endpoint_success


def test_get_issn_year_endpoint_error_handling(repo: JournalRepository) -> None:
    """Verify that API exceptions return None for years."""
    with patch(
        "manuscript_reference_lister.journal_repository.RequestsWrapper.get",
        side_effect=Exception("Timeout"),
    ):
        assert repo.get_journal_year_endpoint("0000-0000", "asc") is None


def test_get_journal_metadata_multiple_issns(repo: JournalRepository) -> None:
    """Verify that journals with multiple ISSNs return distinct records."""
    mock_main = MagicMock(status_code=200)
    mock_main.json.return_value = {
        "message": {
            "items": [
                {
                    "title": "Nature",  # Must contain the exact string
                    "ISSN": ["0028-0836", "1476-4687"],
                }
            ]
        }
    }

    def year_mock(year: int):
        m = MagicMock(status_code=200)
        m.json.return_value = {
            "message": {"items": [{"published-print": {"date-parts": [[year]]}}]}
        }
        return m

    with patch(
        "manuscript_reference_lister.journal_repository.RequestsWrapper.get"
    ) as mock_get:
        mock_get.side_effect = [
            mock_main,
            year_mock(1869),
            year_mock(2023),  # ISSN 1
            year_mock(1997),
            year_mock(2023),  # ISSN 2
        ]

        results = repo.get_journal_metadata("Nature")

        assert len(results) == 2
        assert results[0]["issn"] == "0028-0836"
        assert results[1]["issn"] == "1476-4687"
        assert mock_get.call_count == 5


def test_load_and_merge_all(repo: JournalRepository) -> None:
    """Verify that new titles are merged into the list as empty templates."""
    repo.records = [{"input_title": "Existing", "issn": "0000-0000"}]

    # Mock open for the load part inside the method
    with patch(
        "manuscript_reference_lister.journal_repository.open", mock_open(read_data="[]")
    ):
        repo.load_and_merge_all(journal_title_list=["Existing", "New"])

    assert len(repo.records) == 2
    new_entry = next(i for i in repo.records if i["input_title"] == "New")
    assert new_entry["issn"] is None
    assert new_entry["update"] == str(date.today())


def test_save_all(repo: JournalRepository, tmp_path: Path) -> None:
    """Verify that the journal list is saved correctly to the work directory."""
    repo.records = [{"input_title": "Test", "issn": "1234"}]
    expected_path = tmp_path / repo.local_filename

    repo.save_all()

    assert expected_path.exists()
    with open(expected_path) as f:
        data = json.load(f)
        assert data[0]["input_title"] == "Test"


def test_update_all_priority_and_limit(repo: JournalRepository) -> None:
    """Verify that updates prioritize missing info and respect the max update limit."""
    repo.update_max = 1
    today = date.today()
    old_date = str(today - timedelta(days=45))
    recent_date = str(today - timedelta(days=5))

    repo.records = [
        {"input_title": "Old", "update": old_date, "issn": "1234-5678"},
        {"input_title": "Missing", "update": recent_date, "issn": None},  # Priority
        {"input_title": "Recent", "update": recent_date, "issn": "9012-3456"},
    ]

    updated_data = [
        {"input_title": "Missing", "issn": "1111-2222", "update": str(today)}
    ]

    with patch.object(
        JournalRepository, "get_journal_metadata", return_value=updated_data
    ) as mock_get:
        repo.update_all()

        assert mock_get.call_count == 1
        assert repo.has_pending_updates is True
        # Ensure 'Missing' was the one updated
        assert any(j["issn"] == "1111-2222" for j in repo.records)
