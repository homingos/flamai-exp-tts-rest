import pytest
from fastapi.testclient import TestClient

# By importing 'app', we trigger the sys.path modification inside app.py,
# which makes all other project imports work correctly for pytest.
from app import app

@pytest.fixture(scope="module")
def test_client():
    """Create a TestClient instance for testing the API."""
    client = TestClient(app)
    yield client