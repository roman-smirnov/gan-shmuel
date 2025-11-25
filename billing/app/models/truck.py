from app.utils import get_db_connection
from app.services.weight_client import get_item_from_weight


def create_truck(truck_id, provider_id):
    """
    Register a new truck in the system.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO Trucks (id, provider_id) VALUES (%s, %s)",
        (truck_id, provider_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()


def update_truck(truck_id, provider_id):
    """
    Update a truck's provider assignment.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE Trucks SET provider_id = %s WHERE id = %s",
        (provider_id, truck_id)
    )
    affected_rows = cursor.rowcount
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return affected_rows > 0


def get_truck(truck_id):
    """
    Fetch a truck by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT * FROM Trucks WHERE id = %s",
        (truck_id,)
    )
    truck = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return truck


def get_provider_by_truck(truck_id):
    """
    Get all trucks belonging to a provider.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT provider_id FROM Trucks WHERE id = %s",
        (truck_id,)
    )
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result[0]


def get_trucks_by_provider(provider_id):
    """
    Get all trucks belonging to a provider.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM Trucks WHERE provider_id = %s",
        (provider_id,)
    )
    trucks = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return trucks
def get_truck_sessions(truck_id, from_date, to_date):
    """
    Get truck's tara weight and weighing sessions from Weight service.

    The Weight service returns a list of transactions like:
    [
        {"id": 1, "tara": 5000, "session_id": 123},
        {"id": 2, "tara": 5100, "session_id": 124},
        ...
    ]

    Returns:
        dict: {
            'tara': <int> or 'na',  # last known tara in kg
            'session_ids': [<id1>, <id2>, ...]  # all unique session IDs
        }
    """
    try:
        item_data = get_item_from_weight(truck_id, from_date, to_date)

        # Weight service returns a LIST of transactions
        if not isinstance(item_data, list):
            print(f"Warning: Expected list from weight service, got {type(item_data)}")
            return {
                'tara': 'na',
                'session_ids': []
            }

        # Extract all unique session_ids and find the tara from transaction with highest ID
        session_ids = []
        max_id = None
        tara_from_max_id = None

        # Process each transaction in the list
        for transaction in item_data:
            if not isinstance(transaction, dict):
                continue

            # Collect session_id
            session_id = transaction.get('session_id')
            if session_id is not None and session_id not in session_ids:
                session_ids.append(session_id)

            # Get transaction ID and tara value
            transaction_id = transaction.get('id')
            if transaction_id is None:
                continue

            # Get tara value - check both 'tara' and 'truckTara' keys
            # (Weight service uses 'tara' in API mode, 'truckTara' in UI mode)
            tara = transaction.get('tara') or transaction.get('truckTara')

            # Track the transaction with highest ID that has a valid tara
            if tara is not None and tara != 'na':
                if max_id is None or transaction_id > max_id:
                    max_id = transaction_id
                    tara_from_max_id = tara

        return {
            'tara': tara_from_max_id if tara_from_max_id is not None else 'na',
            'session_ids': session_ids
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error calling weight service for truck {truck_id}: {type(e).__name__}: {str(e)}")
        return {
            'tara': 'na',
            'session_ids': []
        }

