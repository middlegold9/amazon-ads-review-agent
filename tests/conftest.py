import os

os.environ.setdefault("ADS_APPROVE_WRITES", "false")
os.environ.setdefault("ADS_MCP_BASE_URL", "http://localhost:8000")
os.environ.setdefault("ADS_TARGET_ACOS", "0.25")
os.environ.setdefault("ADS_CATEGORY", "default")

import pytest


@pytest.fixture(autouse=True)
def _reset_settings():
    from ads_agent.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
