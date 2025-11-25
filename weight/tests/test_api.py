import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from api.app import init_app, db, Transactions  # import the factory function


@pytest.fixture
def client():
    # pass a test config if you want an in-memory database
    """
    db_user = os.getenv("MYSQL_USER")
    db_pass = os.getenv("MYSQL_PASSWORD")
    db_name = os.getenv("MYSQL_DATABASE")
    db_port = os.getenv("WEIGHT_MYSQL_PORT")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_pass}@weight-db:{db_port}/{db_name}"
    )
    """

    test_config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
    app = init_app(test_config)
    app.config["TESTING"] = True

    with app.app_context():
        # create tables in the in-memory DB
        from api.app import db
        db.create_all()

        # add some initial test data

    # yield the test client outside of app_context to be used in tests
    with app.test_client() as client:
        yield client


@pytest.fixture
def in_truck_payload():
    """Payload for a truck coming in"""
    return {
        "produce": "apples",
        "direction": "in",
        "truck": "TRUCK123",
        "containers": "C1,C2",
        "weight": "2000",
        "unit": "kg",
        "force": "False",
    }


@pytest.fixture
def in_truck_update_payload():
    """Payload for a truck coming in"""
    return {
        "produce": "apples",
        "direction": "in",
        "truck": "TRUCK123",
        "containers": "C1,C2",
        "weight": "1000",
        "unit": "kg",
        "force": "True",
    }


@pytest.fixture
def out_truck_payload():
    """Payload for a truck going out"""
    return {
        "produce": "apples",
        "direction": "out",
        "truck": "TRUCK123",
        "containers": "C1,C2",
        "weight": "1200",
        "unit": "kg",
        "force": "False",
    }


@pytest.fixture()
def out_truck_update_payload():
    """Payload for a truck going out"""
    return {
        "produce": "apples",
        "direction": "out",
        "truck": "TRUCK123",
        "containers": "C1,C2",
        "weight": "1000",
        "unit": "kg",
        "force": "True",
    }


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert b"Service is running" in response.data


def test_basic_post_weight(client, in_truck_payload):
    response = client.post("/weight", data=in_truck_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data["truck"] == in_truck_payload["truck"]
    assert data["bruto"] == int(in_truck_payload["weight"])


def test_post_out_without_in(client, out_truck_payload):
    response = client.post("/weight", data=out_truck_payload)
    assert response.status_code == 409


def test_post_in_twice(client, in_truck_payload):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=in_truck_payload)
    assert second_response.status_code == 409


def test_post_complete_direction_in_out(client, in_truck_payload, out_truck_payload):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=out_truck_payload)
    assert second_response.status_code == 200


def test_post_in_update_force(client, in_truck_payload, in_truck_update_payload):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=in_truck_update_payload)
    assert second_response.status_code == 200


def test_post_out_update_force(
    client, in_truck_payload, out_truck_payload, out_truck_update_payload
):
    first_response = client.post("/weight", data=in_truck_payload)
    assert first_response.status_code == 200
    second_response = client.post("/weight", data=out_truck_payload)
    assert second_response.status_code == 200
    third_response = client.post("/weight", data=out_truck_update_payload)
    assert third_response.status_code == 200
