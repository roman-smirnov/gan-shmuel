import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api.app import init_app, db as _db

# Environment variable to switch between sqlite and mysql for tests
TEST_MODE = os.getenv("TEST_MODE")


def _make_test_config():
    """Return a Flask config dict based on which DB backend we want."""
    if TEST_MODE == "0": # use MySQL DB
        db_user = os.getenv("MYSQL_USER")
        db_pass = os.getenv("MYSQL_PASSWORD")
        db_name = os.getenv("MYSQL_DATABASE")
        db_port = os.getenv("WEIGHT_MYSQL_PORT")

        uri = f"mysql+pymysql://{db_user}:{db_pass}@weight-db:{db_port}/{db_name}"
    else: # use in-memory SQLite DB
        uri = "sqlite:///:memory:"

    return {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = init_app(test_config=_make_test_config())

    with app.app_context():
        _db.create_all()
        yield app
        with app.app_context():
            _db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Give tests direct access to the SQLAlchemy db object if needed."""
    return _db


@pytest.fixture
def in_truck_payload():
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
    return {
        "produce": "apples",
        "direction": "out",
        "truck": "TRUCK123",
        "containers": "C1,C2",
        "weight": "1200",
        "unit": "kg",
        "force": "False",
    }
