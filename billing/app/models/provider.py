from app.utils import get_db_connection

def create_provider(name):

    # Open connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute SQL query
    cursor.execute(
        "INSERT INTO Provider (name) VALUES (%s)",
        (name,)
    )
    provider_id = cursor.lastrowid
    
    # Update changes
    conn.commit()
    # Close connection
    cursor.close()
    conn.close()
    
    return provider_id


def update_provider(provider_id, name):

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
    Fetch a provider by id.
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


def get_provider_by_name(name):
    """
    Fetch a provider by name (for uniqueness check).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT * FROM Provider WHERE name = %s",
        (name,)
    )
    provider = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return provider


def get_all_providers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Provider ORDER BY id")
    providers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return providers
