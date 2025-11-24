from app.utils import get_db_connection
# from app.services.weight_client import get_item_from_weight

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

# ToDo: depends on weight team
# def get_truck_sessions(truck_id, from_date, to_date):
#     """
#     Get truck's tara weight and weighing sessions from Weight service.
#     """
#     try:
#         # Call Weight service's GET /item/<id> endpoint
#         item_data = get_item_from_weight(truck_id, from_date, to_date)
#         return {
#             'tara': item_data.get('tara', 'na'),
#             'session_ids': item_data.get('sessions', [])
#         }
#     except Exception:
#         # Weight service unavailable or error
#         return {
#             'tara': 'na',
#             'session_ids': []
#         }
