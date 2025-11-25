import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from api.app import init_app, db as _db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # in-memory DB for tests
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
    app = init_app(test_config=test_config)

    # Create tables
    with app.app_context():
        _db.create_all()

    yield app

    # Clean up / drop tables
    with app.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()