import logging
import re

logger = logging.getLogger(__name__)


class JournalParser:
    """Handles extraction of journal titles from raw text."""

    def extract_all(self, text: str) -> list[str]:
        """Extract journal titles in a text. The titles should be positioned below a
        line containing only the text Journals, and separated by an EOL."""
        # Matches "Journals" only if it is the only word on the line
        # re.MULTILINE makes ^ and $ work per line
        matches = list(re.finditer(r"^Journals\s*$", text, re.MULTILINE))

        if not matches:
            logger.warning(
                "Section marker 'Journals' not found in the provided text",
                extra={
                    "status": "KO",
                    "event": "journal_marker_missing",
                },
            )
            return []

        # Start from the end of the last "Journals" match
        start_index = matches[-1].end()
        remaining_text = text[start_index:]

        # Look for the first occurrence of two newlines (the "break")
        # \n\s*\n matches a newline, any whitespace/tabs, then another newline
        break_match = re.search(r"\n\s*\n", remaining_text)

        logger.debug(
            "Journal block delimited (Stop on double newline: %s)",
            bool(break_match),
            extra={
                "status": "OK",
                "event": "journal_block_delimited",
                "stopped_by_double_newline": bool(break_match),
            },
        )

        # If a break is found, take everything up to it; otherwise take the rest
        relevant_block = (
            remaining_text[: break_match.start()] if break_match else remaining_text
        )

        # Split into lines, strip whitespace, and filter out empty strings
        results = [line.strip() for line in relevant_block.splitlines() if line.strip()]
        results = list(dict.fromkeys(results))  # unique titles
        logger.info(
            "Extracted %d unique journal titles from section",
            len(results),
            extra={
                "status": "OK",
                "event": "journal_extraction_completed",
                "unique_count": len(results),
            },
        )
        return results
