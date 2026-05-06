import logging

from .parsers import CitationParser, JournalParser
from .repositories import JournalRepository, StyleRepository, WorkRepository
from .utils import DataLoader


def run(
    input_file_path: str | None, input_text: str | None, style: str = "apa"
) -> None:
    """Orchestration of the manuscript-reference-lister pipeline."""
    if not input_text:
        input_text = DataLoader(input_file_path).extract_text_from_docx()
    style_repo = StyleRepository(style)
    style_repo.validate_favored_style()
    if style_repo.favored_style_is_valid is False:
        raise ValueError("Style {style} is not found in crossref api styles.")

    journal_parser = JournalParser()

    journal_required_titles = journal_parser.extract_all(input_text)
    journal_repo = JournalRepository()
    journal_repo.load_all()
    journal_repo.deduplicate()
    journal_repo.merge_new_titles(journal_required_titles)
    journal_repo.update_all()
    journal_repo.save_all()
    file_path = journal_repo.config.local_repo_dir_path / journal_repo.local_filename
    logging.info(f"Saved journal metadata in {file_path}")

    citation_parser = CitationParser()
    citations = citation_parser.extract_all(input_text)

    work_repo = WorkRepository()
    work_repo.load_all()
    work_repo.merge_new_works(citations)
    ISSNs = list({j.ISSN for j in journal_repo.records if j.ISSN is not None})
    work_repo.update_all(ISSNs=ISSNs)
    work_repo.save_all()
