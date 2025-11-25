import pytest
from app import create_app

@pytest.fixture
def client():
    """Create test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_returns_ok(client):
    """Health check should return OK when database is connected."""
    response = client.get('/health')
    assert response.status_code == 800
    assert response.data == b'OK'
