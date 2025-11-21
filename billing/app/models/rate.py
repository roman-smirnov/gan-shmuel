from app.utils import get_db_connection

def save_rates(rates):
    """
    Save rates to database, replacing all existing rates.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Rates")
    
    for rate in rates:
        cursor.execute(
            "INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)",
            (rate['product_id'], rate['rate'], rate['scope'])
        )
    
    conn.commit()
    cursor.close()
    conn.close()


def get_all_rates():
    """
    Fetch all rates from database.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT product_id, rate, scope FROM Rates ORDER BY product_id, scope")
    rates = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rates


def get_rate(product_id, provider_id):
    """
    Get the rate for a product, checking provider-specific rate first.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Try provider-specific rate first
    cursor.execute(
        "SELECT rate FROM Rates WHERE product_id = %s AND scope = %s",
        (product_id, str(provider_id))
    )
    result = cursor.fetchone()
    
    if result:
        cursor.close()
        conn.close()
        return result['rate']
    
    # Fall back to 'ALL' rate
    cursor.execute(
        "SELECT rate FROM Rates WHERE product_id = %s AND scope = 'All'",
        (product_id,)
    )
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result['rate'] if result else 0
