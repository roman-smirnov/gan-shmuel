from flask import Blueprint
from flask import current_app
import socket
import os

# Create Blueprint for health routes
health_bp = Blueprint("health", __name__)


def check_mysql_alive() -> bool:
    try:
        with socket.create_connection((current_app.config['DB_HOST'], current_app.config['DB_PORT']), timeout=1):
            return True
    except OSError:
        return False


@health_bp.get("/health")
def health():
    if check_mysql_alive():
        return "OK", 200     # DB alive
    else:
        return "Failure", 500   # DB is down

