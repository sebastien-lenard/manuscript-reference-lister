import pytest

from manuscript_reference_lister.utils import get_config


@pytest.fixture(autouse=True)
def clear_config_cache():
    """Clear the lru_cache of get_config before each test."""
    get_config.cache_clear()
    yield
