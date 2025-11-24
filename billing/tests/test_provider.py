import pytest
import json
from app import create_app
from app.utils import get_db_connection

@pytest.fixture
def client():
    """Create test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Clean database before each test
        with app.app_context():
            cleanup_database()
        yield client
        # Clean database after each test
        with app.app_context():
            cleanup_database()


def cleanup_database():
    """Delete all test data from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Trucks")
    cursor.execute("DELETE FROM Rates")
    cursor.execute("DELETE FROM Provider")
    
    cursor.execute("ALTER TABLE Provider AUTO_INCREMENT = 10001")
    
    conn.commit()
    cursor.close()
    conn.close()


def test_create_provider_success(client):
    """POST /provider should create a new provider and return ID."""
    response = client.post(
        '/provider',
        data=json.dumps({'name': 'Test Provider'}),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data


def test_create_provider_multiple_names(client):
    """POST /provider should reject duplicate names."""
    # Create first provider
    create_response = client.post(
        '/provider',
        data=json.dumps({'name': 'Same Provider'}),
        content_type='application/json'
    )
    assert create_response.status_code == 201
    
    # Try to create duplicate
    response = client.post(
        '/provider',
        data=json.dumps({'name': 'Same Provider'}),
        content_type='application/json'
    )
    assert response.status_code == 409


def test_create_provider_missing_name(client):
    """POST /provider without name should return 400."""
    response = client.post(
        '/provider',
        data=json.dumps({}),
        content_type='application/json'
    )
    assert response.status_code == 400


def test_create_provider_empty_name(client):
    """POST /provider with empty name should return 400."""
    response = client.post(
        '/provider',
        data=json.dumps({'name': ''}),
        content_type='application/json'
    )
    assert response.status_code == 400


def test_update_provider_success(client):
    """PUT /provider/<id> should update provider name."""
    # First create a provider
    create_response = client.post(
        '/provider',
        data=json.dumps({'name': 'Original Name'}),
        content_type='application/json'
    )
    assert create_response.status_code == 201
    provider_id = json.loads(create_response.data)['id']
    
    # Then update it
    response = client.put(
        f'/provider/{provider_id}',
        data=json.dumps({'name': 'Updated Name'}),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Updated Name'


def test_update_provider_not_found(client):
    """PUT /provider/<id> with invalid ID should return 404."""
    response = client.put(
        '/provider/99999',
        data=json.dumps({'name': 'New Name'}),
        content_type='application/json'
    )
    assert response.status_code == 404


def test_update_provider_duplicate_name(client):
    """PUT /provider/<id> should reject duplicate names."""
    # Create two providers
    response1 = client.post(
        '/provider',
        data=json.dumps({'name': 'Provider One'}),
        content_type='application/json'
    )
    provider1_id = json.loads(response1.data)['id']
    
    response2 = client.post(
        '/provider',
        data=json.dumps({'name': 'Provider Two'}),
        content_type='application/json'
    )
    
    # Try to rename provider 1 to provider 2's name
    response = client.put(
        f'/provider/{provider1_id}',
        data=json.dumps({'name': 'Provider Two'}),
        content_type='application/json'
    )
    assert response.status_code == 409