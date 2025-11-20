from flask import Blueprint
import socket
import os

# Create Blueprint for health routes
health_bp = Blueprint("health", __name__)

# Load environment variables (with defaults)
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")   # default
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))   # default


def check_mysql_alive() -> bool:
    try:
        with socket.create_connection((MYSQL_HOST, MYSQL_PORT), timeout=1):
            return True
    except OSError:
        return False


@health_bp.get("/health")
def health():
    if check_mysql_alive():
        return "OK", 200     # DB alive
    else:
        return "Failure", 500   # DB is down

