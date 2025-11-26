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


def create_test_provider(client, name="Test Provider"):
    """Helper function to create a test provider and return its ID."""
    response = client.post(
        '/provider',
        data=json.dumps({'name': name}),
        content_type='application/json'
    )
    assert response.status_code == 201
    return json.loads(response.data)['id']


# ==================== POST /truck Tests ====================

def test_register_truck_success(client):
    """POST /truck should create a new truck and return 201."""
    provider_id = create_test_provider(client)
    
    response = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': provider_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['id'] == 'TRK-001'
    # Accept both int and string for provider_id
    assert str(data['provider']) == str(provider_id)


def test_register_truck_missing_id(client):
    """POST /truck without id field should return 400."""
    provider_id = create_test_provider(client)
    
    response = client.post(
        '/truck',
        data=json.dumps({'provider': provider_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing fields' in data['error']


def test_register_truck_missing_provider(client):
    """POST /truck without provider field should return 400."""
    response = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001'}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing fields' in data['error']


def test_register_truck_empty_id(client):
    """POST /truck with empty id should return 400."""
    provider_id = create_test_provider(client)
    
    response = client.post(
        '/truck',
        data=json.dumps({'id': '', 'provider': provider_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Truck id cannot be empty'


def test_register_truck_id_too_long(client):
    """POST /truck with id longer than 10 characters should return 400."""
    provider_id = create_test_provider(client)
    
    response = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-123456789', 'provider': provider_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Truck id must be at most 10 characters'


def test_register_truck_invalid_provider_not_integer(client):
    """POST /truck with non-integer provider should return 400."""
    response = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': 'not-a-number'}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Provider must be an integer id'


def test_register_truck_provider_not_found(client):
    """POST /truck with non-existent provider should return 404."""
    response = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': 99999}),
        content_type='application/json'
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Provider not found'


def test_register_truck_already_exists(client):
    """POST /truck with existing truck id should return 409."""
    provider_id = create_test_provider(client)
    
    # Create first truck
    response1 = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': provider_id}),
        content_type='application/json'
    )
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': provider_id}),
        content_type='application/json'
    )
    
    assert response2.status_code == 409
    data = json.loads(response2.data)
    assert data['error'] == 'Truck already exists'
    assert 'message' in data


# ==================== PUT /truck/<id> Tests ====================

def test_update_truck_provider_success(client):
    """PUT /truck/<id> should update truck provider and return 200."""
    provider_id1 = create_test_provider(client, "Provider One")
    provider_id2 = create_test_provider(client, "Provider Two")
    
    # Create truck with provider 1
    create_response = client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': provider_id1}),
        content_type='application/json'
    )
    assert create_response.status_code == 201
    
    # Update to provider 2
    response = client.put(
        '/truck/TRK-001',
        data=json.dumps({'provider': provider_id2}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'TRK-001'
    # Accept both int and string for provider_id
    assert str(data['provider']) == str(provider_id2)


def test_update_truck_empty_id(client):
    """PUT /truck/ with empty id should return 400."""
    provider_id = create_test_provider(client)
    
    response = client.put(
        '/truck/   ',
        data=json.dumps({'provider': provider_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Truck id cannot be empty'


def test_update_truck_missing_provider(client):
    """PUT /truck/<id> without provider field should return 400."""
    provider_id = create_test_provider(client)
    
    # Create truck first
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': provider_id}),
        content_type='application/json'
    )
    
    response = client.put(
        '/truck/TRK-001',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Provider field is required'


def test_update_truck_invalid_provider_not_integer(client):
    """PUT /truck/<id> with non-integer provider should return 400."""
    provider_id = create_test_provider(client)
    
    # Create truck first
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': provider_id}),
        content_type='application/json'
    )
    
    response = client.put(
        '/truck/TRK-001',
        data=json.dumps({'provider': 'not-a-number'}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Provider must be an integer id'


def test_update_truck_not_found(client):
    """PUT /truck/<id> with non-existent truck should return 404."""
    provider_id = create_test_provider(client)
    
    response = client.put(
        '/truck/TRK-999',
        data=json.dumps({'provider': provider_id}),
        content_type='application/json'
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Truck not found'


def test_update_truck_provider_not_found(client):
    """PUT /truck/<id> with non-existent provider should return 404."""
    provider_id = create_test_provider(client)
    
    # Create truck first
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-001', 'provider': provider_id}),
        content_type='application/json'
    )
    
    response = client.put(
        '/truck/TRK-001',
        data=json.dumps({'provider': 99999}),
        content_type='application/json'
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Provider not found'


# ==================== GET /truck/<id> Tests ====================

def test_get_truck_success_with_weight_service(client, mocker):
    """GET /truck/<id> should return truck info with weight service data."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    # Mock weight service
    mock_get_item = mocker.patch('app.models.truck.get_item_from_weight')
    mock_get_item.return_value = [
        {"id": 1, "tara": 5000, "session_id": 101},
        {"id": 2, "tara": 5000, "session_id": 102}
    ]
    
    response = client.get('/truck/TRK-101?from=20251101000000&to=20251123120000')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'TRK-101'
    assert data['tara'] == 5000
    assert data['sessions'] == [101, 102]
    
    # Verify weight service was called with correct parameters
    mock_get_item.assert_called_once_with('TRK-101', '20251101000000', '20251123120000')


def test_get_truck_success_with_default_dates(client, mocker):
    """GET /truck/<id> without dates should use default dates."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    # Mock weight service
    mock_get_item = mocker.patch('app.models.truck.get_item_from_weight')
    mock_get_item.return_value = [
        {"id": 1, "tara": 4500, "session_id": 201}
    ]
    
    response = client.get('/truck/TRK-101')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'TRK-101'
    assert data['tara'] == 4500
    assert data['sessions'] == [201]
    
    # Verify weight service was called (dates will be auto-generated)
    assert mock_get_item.called
    call_args = mock_get_item.call_args[0]
    assert call_args[0] == 'TRK-101'
    assert len(call_args[1]) == 14  # from date format
    assert len(call_args[2]) == 14  # to date format


def test_get_truck_not_found(client):
    """GET /truck/<id> with non-existent truck should return 404."""
    response = client.get('/truck/TRK-999?from=20251101000000&to=20251123120000')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Truck not found'


def test_get_truck_invalid_date_format_from(client):
    """GET /truck/<id> with invalid from date format should return 400."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    response = client.get('/truck/TRK-101?from=2025-11-01&to=20251123120000')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'from/to must be in format yyyymmddhhmmss' in data['error']


def test_get_truck_invalid_date_format_to(client):
    """GET /truck/<id> with invalid to date format should return 400."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    response = client.get('/truck/TRK-101?from=20251101000000&to=2025-11-23')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'from/to must be in format yyyymmddhhmmss' in data['error']


def test_get_truck_invalid_date_length(client):
    """GET /truck/<id> with date not 14 characters should return 400."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    response = client.get('/truck/TRK-101?from=20251101&to=20251123')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'from/to must be in format yyyymmddhhmmss' in data['error']


def test_get_truck_weight_service_error(client, mocker):
    """GET /truck/<id> should handle weight service error gracefully."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    # Mock weight service to raise exception
    mock_get_item = mocker.patch('app.models.truck.get_item_from_weight')
    mock_get_item.side_effect = Exception("Connection error")
    
    response = client.get('/truck/TRK-101?from=20251101000000&to=20251123120000')
    
    # Should still return 200, but with default values
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'TRK-101'
    assert data['tara'] == 'na'
    assert data['sessions'] == []


def test_get_truck_weight_service_returns_na(client, mocker):
    """GET /truck/<id> should handle weight service returning 'na' for tara."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    # Mock weight service to return 'na' for tara
    mock_get_item = mocker.patch('app.models.truck.get_item_from_weight')
    mock_get_item.return_value = {
        'tara': 'na',
        'sessions': []
    }
    
    response = client.get('/truck/TRK-101?from=20251101000000&to=20251123120000')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'TRK-101'
    assert data['tara'] == 'na'
    assert data['sessions'] == []


def test_get_truck_weight_service_empty_sessions(client, mocker):
    """GET /truck/<id> should handle weight service with empty sessions."""
    provider_id = create_test_provider(client)
    
    # Create truck
    client.post(
        '/truck',
        data=json.dumps({'id': 'TRK-101', 'provider': provider_id}),
        content_type='application/json'
    )
    
    # Mock weight service
    mock_get_item = mocker.patch('app.models.truck.get_item_from_weight')
    mock_get_item.return_value = [
        {"id": 1, "tara": 5000, "session_id": None}
    ]
    
    response = client.get('/truck/TRK-101?from=20251101000000&to=20251123120000')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'TRK-101'
    assert data['tara'] == 5000
    assert data['sessions'] == []

