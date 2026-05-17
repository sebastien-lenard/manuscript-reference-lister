import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from manuscript_reference_lister.logging_config import (
    RunIdFilter,
    get_logging_config,
    get_safe_log_dir,
    setup_logging,
)


def test_run_id_filter_injects_uuid() -> None:
    """Verify that RunIdFilter injects a run_id string into the LogRecord."""
    log_filter = RunIdFilter()
    mock_record = MagicMock(spec=logging.LogRecord)

    assert not hasattr(mock_record, "run_id")

    result = log_filter.filter(mock_record)

    assert result is True
    assert hasattr(mock_record, "run_id")
    assert isinstance(mock_record.run_id, str)
    assert len(mock_record.run_id) == 8


def test_get_safe_log_dir_fallback_to_tmp() -> None:
    """Verify that if .env is missing or doesn't have LOG_DIR_PATH, it falls back to the
    OS temporary directory."""
    with patch(
        "manuscript_reference_lister.logging_config.dotenv_values", return_value={}
    ):
        log_dir = get_safe_log_dir()

        expected_dir = Path(tempfile.gettempdir()) / "manuscript-reference-lister"
        assert log_dir == expected_dir


def test_get_safe_log_dir_from_env() -> None:
    """Verify that get_safe_log_dir correctly extracts and cleans the path
    defined in the .env file."""
    mock_env = {"LOG_DIR_PATH": '"C:\\Custom\\Log\\Path"'}

    with patch(
        "manuscript_reference_lister.logging_config.dotenv_values",
        return_value=mock_env,
    ):
        log_dir = get_safe_log_dir()

        assert log_dir == Path("C:\\Custom\\Log\\Path")


@pytest.mark.parametrize(
    "verbose_level, expected_console_level",
    [
        (0, "WARNING"),
        (1, "INFO"),
        (2, "DEBUG"),
        (3, "DEBUG"),  # Maximum verbosity (> 2)
    ],
)
def test_get_logging_config_levels(
    verbose_level: int, expected_console_level: str
) -> None:
    """Verify that the console log level scales correctly with verbosity."""
    dummy_path = Path("/dummy/path")
    config = get_logging_config(dummy_path, verbose_level=verbose_level)

    assert config["handlers"]["console"]["level"] == expected_console_level
    assert config["handlers"]["file"]["filename"] == str(dummy_path / "app.json.log")


def test_setup_logging_creates_directory_and_calls_dictconfig() -> None:
    """Verify that setup_logging triggers directory creation and passes
    the config to Python's logging infrastructure."""
    with (
        patch(
            "manuscript_reference_lister.logging_config.get_safe_log_dir"
        ) as mock_get_dir,
        patch("pathlib.Path.mkdir"),
        patch("logging.config.dictConfig") as mock_dict_config,
    ):
        mock_path = MagicMock(spec=Path)
        mock_get_dir.return_value = mock_path

        setup_logging(verbose_level=1)

        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_dict_config.assert_called_once()
