import pytest

from manuscript_reference_lister.network.http_client_registry import (
    get_http_client_registry,
)
from manuscript_reference_lister.utils import get_config


@pytest.fixture(autouse=True)
def _clear_config_cache():
    """Clear the lru_cache of get_config before each test."""
    get_config.cache_clear()
    yield


@pytest.fixture(autouse=True)
def _clear_registry_cache() -> None:
    """Automatically clear the lru_cache of get_registry before each test."""
    get_http_client_registry.cache_clear()
