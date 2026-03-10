"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import os


@pytest.fixture
def temp_dir():
    """Provide a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables."""
    original_env = dict(os.environ)
    os.environ["OPEN_GRACE_ENV"] = "test"
    yield
    os.environ.clear()
    os.environ.update(original_env)