import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from manuscript_reference_lister.repositories import BaseRepository
from manuscript_reference_lister.schemas import BaseSchema
from manuscript_reference_lister.utils import AppConfig, get_config


@dataclass
class MockSchema(BaseSchema):
    """Simple schema for testing repository logic."""

    id: int
    content: str = "test"

    @property
    def identity_key(self) -> int:
        return self.id


class MockRepository(BaseRepository[MockSchema]):
    """Concrete repository for testing base logic."""

    pass


@pytest.fixture
def base_repo(tmp_path: Path) -> MockRepository:
    """Fixture providing a repo pointing to a temporary directory."""
    current_cfg = get_config()
    test_config = AppConfig(**{**current_cfg.__dict__, "local_repo_dir_path": tmp_path})
    return MockRepository("test_base_records.json", MockSchema, config=test_config)


def test_deduplicate_removes_repeats(base_repo: MockRepository) -> None:
    """Ensure records with identical identity_keys are removed, keeping the first."""
    base_repo.records = [
        MockSchema(id=1, content="first"),
        MockSchema(id=2, content="unique"),
        MockSchema(id=1, content="duplicate"),
    ]

    base_repo.deduplicate()

    assert len(base_repo) == 2
    assert base_repo.records[0].content == "first"
    assert [r.id for r in base_repo.records] == [1, 2]


def test_load_all_success(base_repo: MockRepository) -> None:
    """Verify raw JSON data is correctly instantiated into schema objects."""
    path = Path(base_repo.config.local_repo_dir_path) / base_repo.local_filename
    valid_data = [{"id": 1, "content": "A"}, {"id": 2, "content": "B"}]
    path.write_text(json.dumps(valid_data))

    base_repo.load_all()

    assert len(base_repo) == 2
    assert isinstance(base_repo.records[0], MockSchema)
    assert base_repo.records[0].id == 1


def test_load_all_invalid_schema(base_repo: MockRepository) -> None:
    """Verify records list is cleared if data fails schema validation."""
    path = Path(base_repo.config.local_repo_dir_path) / base_repo.local_filename
    # Missing required 'id' field
    invalid_data = [{"content": "broken"}]
    path.write_text(json.dumps(invalid_data))

    base_repo.load_all()

    assert base_repo.records == []
    assert len(base_repo) == 0


def test_load_all_file_not_found(base_repo: MockRepository) -> None:
    """Verify that a missing file results in empty records without crashing."""
    missing_path = Path(base_repo.config.local_repo_dir_path) / base_repo.local_filename
    if missing_path.exists():
        missing_path.unlink()
    base_repo.load_all()
    assert base_repo.records == []
    assert base_repo._load_failed is False


def test_save_all_atomic_success(base_repo: MockRepository, tmp_path: Path) -> None:
    """Verify save_all writes JSON and cleans up temporary files."""
    data = [MockSchema(id=1, content="saved")]
    base_repo.records = data
    target = tmp_path / base_repo.local_filename

    base_repo.save_all(output_filepath=target)

    assert target.exists()
    assert json.loads(target.read_text())[0]["id"] == 1
    # Check that temp file is cleaned up
    assert not target.with_suffix(".tmp").exists()


def test_save_all_overwrite_existing(base_repo: MockRepository) -> None:
    """Verify that save_all correctly overwrites an existing file via atomic swap."""
    path = Path(base_repo.config.local_repo_dir_path) / base_repo.local_filename
    path.write_text("initial junk data")

    new_record = MockSchema(id=99, content="new")
    base_repo.records = [new_record]
    base_repo.save_all()

    saved_data = json.loads(path.read_text())
    assert len(saved_data) == 1
    assert saved_data[0]["id"] == 99
