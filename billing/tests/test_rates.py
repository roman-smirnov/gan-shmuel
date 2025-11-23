import json
import pytest
from app import create_app
from app.utils import get_db_connection
from app.routes import rates as rates_module


@pytest.fixture
def client():
    """Create test client + clean DB each time."""
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            cleanup_database()
        yield client
        with app.app_context():
            cleanup_database()


def cleanup_database():
    """Clean database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Trucks")
    cursor.execute("DELETE FROM Rates")
    cursor.execute("DELETE FROM Provider")
    cursor.execute("ALTER TABLE Provider AUTO_INCREMENT = 10001")
    conn.commit()
    cursor.close()
    conn.close()


# ================================
# POST /rates – tests
# ================================

def test_post_rates_success(client, monkeypatch):
    """Valid file + valid data → should save 3 rows in DB."""

    monkeypatch.setattr(rates_module.os.path, "exists", lambda path: True)

    def fake_parse(filepath):
        return [
            {"product_id": "1", "rate": 50, "scope": "ALL"},
            {"product_id": "1", "rate": 70, "scope": "10001"},
            {"product_id": "2", "rate": 40, "scope": "ALL"},
        ]

    monkeypatch.setattr(rates_module, "parse_rates_file", fake_parse)

    response = client.post(
        "/rates",
        data=json.dumps({"file": "rates.xlsx"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert data["count"] == 3


def test_post_rates_missing_file_param(client):
    """Missing 'file' field → 400"""
    response = client.post(
        "/rates",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert json.loads(response.data)["error"] == "file parameter is required"


def test_post_rates_empty_list_from_parser(client, monkeypatch):
    """parse_rates_file() returns empty list → 400"""
    monkeypatch.setattr(rates_module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(rates_module, "parse_rates_file", lambda filepath: [])
    response = client.post(
        "/rates",
        data=json.dumps({"file": "empty.xlsx"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert json.loads(response.data)["error"] == "No rates found in file"


def test_post_rates_invalid_format_value_error(client, monkeypatch):
    """parse_rates_file() raises ValueError → 400"""
    monkeypatch.setattr(rates_module.os.path, "exists", lambda path: True)

    def fake_parse(filepath):
        raise ValueError("Bad format")

    monkeypatch.setattr(rates_module, "parse_rates_file", fake_parse)

    response = client.post(
        "/rates",
        data=json.dumps({"file": "bad.xlsx"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Invalid file format" in json.loads(response.data)["error"]


# ================================
# GET /rates – tests
# ================================

def test_get_rates_empty_db(client):
    """DB is empty → return 404"""
    response = client.get("/rates")
    assert response.status_code == 404
    assert json.loads(response.data)["error"] == "No rates found in the database."


def test_get_rates_returns_200_when_db_has_data(client):
    """
    If DB contains at least one row → GET /rates should return 200 OK.
    (We don't check the Excel file content here.)
    """

    # 1) Insert at least one row into DB – inside app context
    with client.application.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Rates (product_id, rate, scope) VALUES (%s, %s, %s)",
            ("1", 50, "ALL")
        )
        conn.commit()
        cursor.close()
        conn.close()

    # 2) Call endpoint
    response = client.get("/rates")

    # 3) Only check status code
    assert response.status_code == 200

