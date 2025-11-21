from app.utils import get_db_connection

def create_provider(name):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Provider (name) VALUES (%s)",
        (name,)
    )
    provider_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return provider_id


def update_provider(provider_id, name):
    """
    Update an existing provider's name.
    
    Args:
        provider_id: Provider's ID
        name: New name
    
    Returns:
        bool: True if a row was updated, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE Provider SET name = %s WHERE id = %s",
        (name, provider_id)
    )
    affected_rows = cursor.rowcount
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return affected_rows > 0


def get_provider(provider_id):
    """
    Fetch a provider by ID.
    
    Args:
        provider_id: Provider's ID
    
    Returns:
        dict: Provider data {'id': ..., 'name': ...} or None if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT * FROM Provider WHERE id = %s",
        (provider_id,)
    )
    provider = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return provider


def get_all_providers():
    """
    Fetch all providers.
    
    Returns:
        list: List of provider dicts
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Provider ORDER BY id")
    providers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return providers
