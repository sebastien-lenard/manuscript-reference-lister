import logging
import time
from datetime import date, datetime, timedelta
from typing import Literal

from manuscript_reference_lister.schemas import JournalMetadata
from manuscript_reference_lister.utils import AppConfig

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class JournalRepository(BaseRepository[JournalMetadata]):
    """Handles journal metadata records."""

    def __init__(
        self,
        local_filename: str = "journal_records.json",
        config: AppConfig | None = None,
    ):
        super().__init__(local_filename, model_class=JournalMetadata, config=config)
        self.has_pending_updates = False

    def get_journal_metadata(self, input_title: str) -> list[JournalMetadata]:
        """
        Get journal metadata filtered on the exact match of the title (input_title) that
        have published works. A title can correspond to several records or none, each of
        them identified by a unique ISSN.
        Warning: If more than 1 exact match is found, returns only the records for the
        first one found.
        """
        logger.info(
            "Retrieving journal %s metadata from Crossref...",
            input_title,
            extra={
                "status": "OK",
                "event": "crossref_journal_query_start",
                "input_title": input_title,
            },
        )
        # Retrieval of records with titles similar to input_title from Crossref API
        params = {
            "query": input_title,
            "rows": 200,  # Large batch to find all matches
            "mailto": self.config.crossref_api_email,
        }

        journal_records = []
        response = self.http_client_wrapper.get(
            self.config.crossref_api_journals_url, params=params, headers=self.headers
        )
        response.raise_for_status()

        items = response.json().get("message", {}).get("items", [])

        # Discard records without exact title match
        exact_matches = [
            item for item in items if item.get("title", "").strip() == input_title
        ]

        if not exact_matches:
            logger.warning(
                "Journal %s not found.",
                input_title,
                extra={
                    "status": "KO",
                    "event": "crossref_journal_not_found",
                    "input_title": input_title,
                },
            )
            return [JournalMetadata(input_title=input_title)]

        # Discard exact matches other than the 1st one
        if len(exact_matches) > 1:
            logger.warning(
                "Discarded %d duplicate titles in the repo for journal: %s",
                len(exact_matches),
                input_title,
                extra={
                    "status": "WARNING",
                    "event": "crossref_duplicate_titles_discarded",
                    "discarded_count": len(exact_matches),
                    "input_title": input_title,
                },
            )
        item = exact_matches[0]
        true_title = item.get("title", "")
        publisher = item.get("publisher", "")
        issns = list(dict.fromkeys(item.get("ISSN", [])))  # remove duplicate ISSNs

        for issn in issns:
            logger.info(
                "Retrieving %s / %s publication range...",
                input_title,
                issn,
                extra={
                    "status": "OK",
                    "event": "crossref_issn_range_query_start",
                    "input_title": input_title,
                    "issn": issn,
                },
            )
            # Publication range
            dates = {
                "min_year": self.get_issn_year_endpoint(issn, "asc"),
                "max_year": self.get_issn_year_endpoint(issn, "desc"),
            }

            # Discard records without published work
            if not dates["min_year"] or not dates["max_year"]:
                logger.warning(
                    "Skipping journal %s / %s (no published work found)",
                    input_title,
                    issn,
                    extra={
                        "status": "WARNING",
                        "event": "crossref_journal_skipped_no_works",
                        "input_title": input_title,
                        "issn": issn,
                    },
                )
                continue

            journal_records.append(
                JournalMetadata(
                    input_title=input_title,
                    true_title=true_title,
                    publisher=publisher,
                    ISSN=issn,
                    start_year=dates["min_year"],
                    end_year=dates["max_year"],
                )
            )
        return journal_records

    def get_issn_year_endpoint(
        self, issn: str, order: Literal["asc", "desc"]
    ) -> int | None:
        """Get the year of the oldest (order: asc) or the newest (order: desc) published
        work (no distinction print or online) for the ISSN."""
        params = {
            "sort": "published",
            "order": order,
            "rows": 1,
            "mailto": self.config.crossref_api_email,
        }
        response = self.http_client_wrapper.get(
            self.config.crossref_api_journals_issn_url.replace("{issn}", str(issn)),
            params=params,
            headers=self.headers,
        )

        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        if not items:
            return None

        work = items[0]
        p_date = work.get("published-print", {}).get("date-parts", [[None]])[0][0]
        o_date = work.get("published-online", {}).get("date-parts", [[None]])[0][0]

        # Earliest or latest year found between print/online
        years = [y for y in [p_date, o_date] if y is not None]
        return min(years) if order == "asc" and years else max(years) if years else None

    def update_all(self) -> None:
        """Update the records missing metadata (Priority 1) and records with expired
        metadata (Priority 2) with up-to-date metatata from the remote repo.
        Warning: Update restricted to a max number of journals, doesn't include
        regular local saving of the updates."""

        expiration_date = date.today() - timedelta(days=self.config.journal_update_days)
        logger.info(
            "Updating journals without metadata or metadata older than: %s",
            expiration_date,
            extra={
                "status": "OK",
                "event": "journal_update_process_started",
                "expiration_threshold": str(expiration_date),
            },
        )
        missing_metadata: list[JournalMetadata] = []
        expired_metadata: list[JournalMetadata] = []
        valid_metadata: list[JournalMetadata] = []

        for record in self.records:
            last_update = datetime.strptime(record.update, "%Y-%m-%d").date()

            has_missing_data = any(v is None for v in record.model_dump().values())
            if has_missing_data:
                missing_metadata.append(record)
            elif last_update < expiration_date:
                expired_metadata.append(record)
            else:
                valid_metadata.append(record)

        logger.info(
            "Journal categorization completed. Missing: %d, Expired: %d, Valid: %d",
            len(missing_metadata),
            len(expired_metadata),
            len(valid_metadata),
            extra={
                "status": "OK",
                "event": "journal_update_categorization",
                "missing_count": len(missing_metadata),
                "expired_count": len(expired_metadata),
                "valid_count": len(valid_metadata),
            },
        )

        records_to_update = missing_metadata + expired_metadata

        update_count = 0
        last_display_time = time.time()
        update_total = len(records_to_update)
        update_remaining = 0

        for i, record in enumerate(records_to_update):
            if update_count < self.config.journal_update_limit:
                new_data = self.get_journal_metadata(record.input_title)
                if new_data:
                    valid_metadata.extend(new_data)
                else:
                    valid_metadata.append(record)
                update_count += 1
            else:
                # We hit the limit; keep the old record and count it for the warning
                valid_metadata.append(record)
                update_remaining = len(records_to_update) - i
                break
            # Display update every 10 seconds
            if time.time() - last_display_time > 10:
                remaining = update_total - (i + 1)
                logger.info(
                    "Batch update status: %d updates remaining out of %d",
                    remaining,
                    update_total,
                    extra={
                        "status": "OK",
                        "event": "journal_update_heartbeat",
                        "remaining_count": remaining,
                        "total_count": update_total,
                    },
                )
                last_display_time = time.time()

        # 3. Handle Warning and Flag
        if update_remaining > 0:
            self.has_pending_updates = True
            logger.warning(
                "Journal update limit reached. %d records still need updating.",
                update_remaining,
                extra={
                    "status": "WARNING",
                    "event": "journal_update_limit_reached",
                    "remaining_count": update_remaining,
                    "limit_configured": self.config.journal_update_limit,
                },
            )

        self.records = valid_metadata
        logger.info(
            "Journal metadata sync finalized. Updated %d journals",
            len(valid_metadata),
            extra={
                "status": "OK",
                "event": "journal_update_completed",
                "total_records": len(valid_metadata),
            },
        )

    def merge_new_titles(self, input_titles: list[str]) -> None:
        """Merge new titles into the existing records as empty templates.
        No duplication of titles."""
        input_titles = list(dict.fromkeys(input_titles))  # unique titles
        # Set for fast lookup
        existing_titles = {info.input_title for info in self.records}

        new_entries = [
            JournalMetadata(input_title=title)
            for title in input_titles
            if title not in existing_titles
        ]

        self.records.extend(new_entries)
        logger.info(
            "Merged %d new journal records into the local repository list",
            len(new_entries),
            extra={
                "status": "OK",
                "event": "journal_records_merged",
                "new_entries_count": len(new_entries),
            },
        )
