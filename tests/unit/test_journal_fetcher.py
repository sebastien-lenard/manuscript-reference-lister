import json
import logging
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from manuscript_reference_lister import JournalFetcher


@pytest.fixture
def fetcher(tmp_path: Path) -> JournalFetcher:
    """Provides a JournalFetcher instance configured with a temporary work directory."""
    fetcher = JournalFetcher()
    fetcher.work_dir_path = str(tmp_path)
    return fetcher


def test_get_issns_and_dates_by_name_success(fetcher: JournalFetcher) -> None:
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
        "manuscript_reference_lister.journal_fetcher.RequestsWrapper.get"
    ) as mock_get:
        mock_get.side_effect = [mock_main, mock_year, mock_year]

        results = fetcher.get_issns_and_dates_by_name("Geology")

        assert len(results) == 1
        assert results[0]["issn"] == "0091-7613"
        assert results[0]["start_year"] == 1973
        assert results[0]["end_year"] == 1995


def test_get_issns_and_dates_not_found_behavior(
    fetcher: JournalFetcher, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify fallback to template and warning log when no journal is found."""
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"message": {"items": []}}

    with patch(
        "manuscript_reference_lister.journal_fetcher.RequestsWrapper.get",
        return_value=mock_resp,
    ):
        with caplog.at_level(logging.WARNING):
            results = fetcher.get_issns_and_dates_by_name("Unknown Journal")

            assert any(
                "Unknown Journal not found" in record.message
                for record in caplog.records
            )
            assert len(results) == 1
            assert results[0]["issn"] is None
            assert results[0]["requested_title"] == "Unknown Journal"


def test_get_year_endpoint_error_handling(fetcher: JournalFetcher) -> None:
    """Verify that API exceptions return None for years."""
    with patch(
        "manuscript_reference_lister.journal_fetcher.RequestsWrapper.get",
        side_effect=Exception("Timeout"),
    ):
        assert fetcher.get_year_endpoint("0000-0000", "asc") is None


def test_get_issns_and_dates_multiple_issns(fetcher: JournalFetcher) -> None:
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
        "manuscript_reference_lister.journal_fetcher.RequestsWrapper.get"
    ) as mock_get:
        mock_get.side_effect = [
            mock_main,
            year_mock(1869),
            year_mock(2023),  # ISSN 1
            year_mock(1997),
            year_mock(2023),  # ISSN 2
        ]

        results = fetcher.get_issns_and_dates_by_name("Nature")

        assert len(results) == 2
        assert results[0]["issn"] == "0028-0836"
        assert results[1]["issn"] == "1476-4687"
        assert mock_get.call_count == 5


def test_load_and_merge_journal_info_list(fetcher: JournalFetcher) -> None:
    """Verify that new titles are merged into the list as empty templates."""
    fetcher.journal_info_list = [{"requested_title": "Existing", "issn": "0000-0000"}]

    # Mock open for the load_journal_info_list part inside the method
    with patch(
        "manuscript_reference_lister.journal_fetcher.open", mock_open(read_data="[]")
    ):
        fetcher.load_and_merge_journal_info_list(journal_title_list=["Existing", "New"])

    assert len(fetcher.journal_info_list) == 2
    new_entry = next(
        i for i in fetcher.journal_info_list if i["requested_title"] == "New"
    )
    assert new_entry["issn"] is None
    assert new_entry["update"] == str(date.today())


def test_save_journal_info_list(fetcher: JournalFetcher, tmp_path: Path) -> None:
    """Verify that the journal list is saved correctly to the work directory."""
    fetcher.journal_info_list = [{"requested_title": "Test", "issn": "1234"}]
    expected_path = tmp_path / "journal_info_list.json"

    fetcher.save_journal_info_list()

    assert expected_path.exists()
    with open(expected_path) as f:
        data = json.load(f)
        assert data[0]["requested_title"] == "Test"


def test_update_journal_info_priority_and_limit(fetcher: JournalFetcher) -> None:
    """Verify that updates prioritize missing info and respect the max update limit."""
    fetcher.update_max = 1
    today = date.today()
    old_date = str(today - timedelta(days=45))
    recent_date = str(today - timedelta(days=5))

    fetcher.journal_info_list = [
        {"requested_title": "Old", "update": old_date, "issn": "1234-5678"},
        {"requested_title": "Missing", "update": recent_date, "issn": None},  # Priority
        {"requested_title": "Recent", "update": recent_date, "issn": "9012-3456"},
    ]

    updated_data = [
        {"requested_title": "Missing", "issn": "1111-2222", "update": str(today)}
    ]

    with patch.object(
        JournalFetcher, "get_issns_and_dates_by_name", return_value=updated_data
    ) as mock_get:
        fetcher.update_journal_info()

        assert mock_get.call_count == 1
        assert fetcher.has_pending_updates is True
        # Ensure 'Missing' was the one updated
        assert any(j["issn"] == "1111-2222" for j in fetcher.journal_info_list)
