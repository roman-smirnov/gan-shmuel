# =============================================================================
# BILLING ENDPOINT TESTS
# =============================================================================
# Tests for GET /bill/<id> endpoint with mocked Weight service

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
        yield client


@pytest.fixture(autouse=True)
def cleanup_database(client):
    """Clean database before and after each test."""
    with client.application.app_context():
        cleanup_db()
    yield
    with client.application.app_context():
        cleanup_db()


def cleanup_db():
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
    """Helper to create a provider."""
    response = client.post(
        '/provider',
        data=json.dumps({'name': name}),
        content_type='application/json'
    )
    return json.loads(response.data)['id']


def create_test_truck(client, truck_id, provider_id):
    """Helper to register a truck."""
    response = client.post(
        '/truck',
        data=json.dumps({'id': truck_id, 'provider': provider_id}),
        content_type='application/json'
    )
    return response.status_code == 201


def upload_test_rates(client):
    """Helper to insert test rates directly into database."""
    with client.application.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert standard test rates
        cursor.execute("INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)", ('Navel', 93, 'All'))
        cursor.execute("INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)", ('Mandarin', 104, 'All'))
        cursor.execute("INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)", ('Blood', 112, 'All'))
        cursor.execute("INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)", ('Tangerine', 92, 'All'))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    return True


# =============================================================================
# SUCCESS CASES
# =============================================================================

def test_bill_success_with_two_products(client, mocker):
    """Test successful bill calculation with multiple products."""
    # Setup
    provider_id = create_test_provider(client, "Fresh Farms")
    create_test_truck(client, "T-14409", provider_id)
    create_test_truck(client, "T-16474", provider_id)
    upload_test_rates(client)
    
    # Mock Weight API response
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.side_effect = [
        # First call: GET /weight
        {
            'results': [
                {
                    'id': 1001,
                    'direction': 'in',
                    'bruto': 10000,
                    'neto': 8500,
                    'produce': 'Navel',
                    'containers': 'C-35434,C-73281'
                },
                {
                    'id': 1002,
                    'direction': 'in',
                    'bruto': 9500,
                    'neto': 7800,
                    'produce': 'Mandarin',
                    'containers': 'C-35537'
                },
                {
                    'id': 1003,
                    'direction': 'in',
                    'bruto': 11000,
                    'neto': 9200,
                    'produce': 'Navel',
                    'containers': 'C-49036,C-85957'
                }
            ]
        },
        # Second call: GET /session/1001
        {'id': 1001, 'truck': 'T-14409', 'bruto': 10000, 'neto': 8500},
        # Third call: GET /session/1002
        {'id': 1002, 'truck': 'T-14409', 'bruto': 9500, 'neto': 7800},
        # Fourth call: GET /session/1003
        {'id': 1003, 'truck': 'T-16474', 'bruto': 11000, 'neto': 9200}
    ]
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    # Test
    response = client.get(f'/bill/{provider_id}')
    
    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['id'] == str(provider_id)
    assert data['name'] == 'Fresh Farms'
    assert data['truckCount'] == 2
    assert data['sessionCount'] == 3
    assert len(data['products']) == 2
    
    # Check products
    products_by_name = {p['product']: p for p in data['products']}
    
    mandarin = products_by_name['Mandarin']
    assert mandarin['count'] == '1'
    assert mandarin['amount'] == 7800
    assert mandarin['rate'] == 104
    assert mandarin['pay'] == 7800 * 104
    
    navel = products_by_name['Navel']
    assert navel['count'] == '2'
    assert navel['amount'] == 8500 + 9200
    assert navel['rate'] == 93
    assert navel['pay'] == (8500 + 9200) * 93
    
    assert data['total'] == (7800 * 104) + ((8500 + 9200) * 93)


def test_bill_with_custom_date_range(client, mocker):
    """Test bill with custom date range parameters."""
    provider_id = create_test_provider(client)
    create_test_truck(client, "T-14409", provider_id)
    upload_test_rates(client)
    
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.return_value = {'results': []}
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    response = client.get(f'/bill/{provider_id}?from=20240101000000&to=20240131235959')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['from'] == '20240101000000'
    assert data['to'] == '20240131235959'
    
    # Verify Weight API was called with correct dates
    call_args = mock_get.call_args
    assert call_args[1]['params']['from'] == '20240101000000'
    assert call_args[1]['params']['to'] == '20240131235959'


def test_bill_filters_by_provider_trucks_only(client, mocker):
    """Test that bill only includes sessions from provider's trucks."""
    # Create two providers
    provider1 = create_test_provider(client, "Provider 1")
    provider2 = create_test_provider(client, "Provider 2")
    
    create_test_truck(client, "T-14409", provider1)
    create_test_truck(client, "T-16474", provider2)
    
    upload_test_rates(client)
    
    # Mock returns sessions for BOTH trucks
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.side_effect = [
        {
            'results': [
                {'id': 1001, 'direction': 'in', 'bruto': 10000, 'neto': 8500, 'produce': 'Navel', 'containers': 'C-001'},
                {'id': 1002, 'direction': 'in', 'bruto': 9500, 'neto': 7800, 'produce': 'Mandarin', 'containers': 'C-002'},
                {'id': 1003, 'direction': 'in', 'bruto': 11000, 'neto': 9200, 'produce': 'Navel', 'containers': 'C-003'}
            ]
        },
        {'id': 1001, 'truck': 'T-14409', 'neto': 8500},
        {'id': 1002, 'truck': 'T-14409', 'neto': 7800},
        {'id': 1003, 'truck': 'T-16474', 'neto': 9200}
    ]
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    # Get bill for provider 1
    response = client.get(f'/bill/{provider1}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Provider 1 should only see sessions from T-14409 (2 sessions)
    assert data['sessionCount'] == 2
    assert data['truckCount'] == 1


# =============================================================================
# EDGE CASES
# =============================================================================

def test_bill_with_na_weights(client, mocker):
    """Test that sessions with 'na' neto are skipped."""
    provider_id = create_test_provider(client)
    create_test_truck(client, "T-14409", provider_id)
    upload_test_rates(client)
    
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.side_effect = [
        {
            'results': [
                {'id': 2001, 'direction': 'in', 'bruto': 10000, 'neto': 'na', 'produce': 'Navel', 'containers': 'C-001'},
                {'id': 2002, 'direction': 'in', 'bruto': 9500, 'neto': 7800, 'produce': 'Mandarin', 'containers': 'C-002'}
            ]
        },
        {'id': 2001, 'truck': 'T-14409', 'neto': 'na'},
        {'id': 2002, 'truck': 'T-14409', 'neto': 7800}
    ]
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    response = client.get(f'/bill/{provider_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Only 1 product (Mandarin)
    assert len(data['products']) == 1
    assert data['products'][0]['product'] == 'Mandarin'


def test_bill_with_no_sessions(client, mocker):
    """Test bill when provider has no weighing sessions."""
    provider_id = create_test_provider(client)
    create_test_truck(client, "T-14409", provider_id)
    upload_test_rates(client)
    
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.return_value = {'results': []}
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    response = client.get(f'/bill/{provider_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['sessionCount'] == 0
    assert data['products'] == []
    assert data['total'] == 0


def test_bill_with_no_trucks(client, mocker):
    """Test bill when provider has no registered trucks."""
    provider_id = create_test_provider(client)
    upload_test_rates(client)
    
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.return_value = {'results': []}
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    response = client.get(f'/bill/{provider_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['truckCount'] == 0
    assert data['sessionCount'] == 0
    assert data['products'] == []
    assert data['total'] == 0


# =============================================================================
# ERROR CASES
# =============================================================================

def test_bill_provider_not_found(client):
    """Test bill for non-existent provider returns 404."""
    response = client.get('/bill/99999')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_bill_invalid_date_format(client):
    """Test bill with invalid date format returns 400."""
    provider_id = create_test_provider(client)
    
    response = client.get(f'/bill/{provider_id}?from=2024-01-01&to=2024-12-31')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid' in data['error']


def test_bill_weight_service_unavailable(client, mocker):
    """Test bill when Weight service is down returns 500."""
    provider_id = create_test_provider(client)
    create_test_truck(client, "T-14409", provider_id)
    
    # Mock connection error
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.side_effect = Exception("Connection refused")
    
    response = client.get(f'/bill/{provider_id}')
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data


def test_bill_with_provider_specific_rates(client, mocker):
    """Test that provider-specific rates override global rates."""
    provider_id = create_test_provider(client)
    create_test_truck(client, "T-14409", provider_id)
    
    # Manually insert provider-specific rate
    with client.application.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)", ('Mandarin', 120, str(provider_id)))
        cursor.execute("INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)", ('Mandarin', 104, 'All'))
        cursor.execute("INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)", ('Navel', 93, 'All'))
        conn.commit()
        cursor.close()
        conn.close()
    
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.side_effect = [
        {
            'results': [
                {'id': 1002, 'direction': 'in', 'bruto': 9500, 'neto': 7800, 'produce': 'Mandarin', 'containers': 'C-002'}
            ]
        },
        {'id': 1002, 'truck': 'T-14409', 'neto': 7800}
    ]
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    response = client.get(f'/bill/{provider_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Should use provider-specific rate (120) instead of global (104)
    mandarin = data['products'][0]
    assert mandarin['rate'] == 120
    assert mandarin['pay'] == 7800 * 120


def test_bill_default_dates(client, mocker):
    """Test that default dates are 1st of month and now."""
    from datetime import datetime
    
    provider_id = create_test_provider(client)
    create_test_truck(client, "T-14409", provider_id)
    
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.return_value = {'results': []}
    
    mock_get = mocker.patch('app.services.weight_client.requests.get')
    mock_get.return_value = mock_response
    
    response = client.get(f'/bill/{provider_id}')
    
    assert response.status_code == 200
    
    # Check dates were passed to Weight API
    call_args = mock_get.call_args
    from_date = call_args[1]['params']['from']
    to_date = call_args[1]['params']['to']
    
    # Check default from date is 1st of current month
    assert from_date[6:8] == '01'  # Day is 01
    assert from_date[8:] == '000000'  # Time is 000000
    
    # Check default to date is current time (roughly)
    now = datetime.now()
    assert to_date[:8] == now.strftime('%Y%m%d')  # Same day