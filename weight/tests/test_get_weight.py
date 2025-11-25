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


def test_get_transactions(client, in_truck_payload, out_truck_payload):
    client.post("/weight", data=in_truck_payload)
    client.post("/weight", data=out_truck_payload) 
    response = client.get("/weight")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3
