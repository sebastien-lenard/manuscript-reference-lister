import logging
from unittest.mock import patch

import pytest

from manuscript_reference_lister.network.http_client_registry import (
    get_http_client_registry,
)
from manuscript_reference_lister.utils import create_config, get_config


@pytest.fixture(autouse=True)
def _clear_config_cache():
    """Clear the lru_cache of get_config before each test."""
    get_config.cache_clear()
    yield


@pytest.fixture(autouse=True)
def _clear_registry_cache() -> None:
    """Automatically clear the lru_cache of get_registry before each test."""
    get_http_client_registry.cache_clear()


@pytest.fixture(autouse=True)
def assert_logging_integrity(caplog):
    """Safeguard of log handlers. Insert a unique token in logs and check its survival
    at the end of the test"""
    yield

    caplog.set_level(logging.INFO)
    canary_message = "LOGGING_INTEGRITY_CHECK_CANARY_TOKEN"

    logging.getLogger("manuscript_reference_lister").info(canary_message)

    if canary_message not in caplog.text:
        raise AssertionError(
            "CRITICAL: This test broke the global logging propagation! "
            "This usually happens when `setup_logging()` or `logging.basicConfig()` "
            "is called by the production code without being mocked. "
            "Please ensure you apply a proper patch/mock in this test script."
        )


@pytest.fixture
def test_config(tmp_path):
    """Test configuration isolated with temporary directories."""
    config_instance = create_config()
    test_config_obj = config_instance.model_copy(
        update={
            "local_repo_dir_path": tmp_path,
            "log_dir_path": tmp_path,
            "output_dir_path": tmp_path,
        }
    )

    with patch(
        "manuscript_reference_lister.utils.config.get_config",
        return_value=test_config_obj,
    ):
        yield test_config_obj
