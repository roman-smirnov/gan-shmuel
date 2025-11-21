import mysql.connector
from flask import current_app

def get_db_connection():
    """Create and return a new database connection."""
    return mysql.connector.connect(
        host=current_app.config['DB_HOST'],
        user=current_app.config['DB_USER'],
        password=current_app.config['DB_PASSWORD'],
        database=current_app.config['DB_NAME']
    )