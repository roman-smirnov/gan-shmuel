from flask import Flask
from .config import Config
from .routes.health import health_bp
from .routes.provider import providers_bp
'''from .routes.providers import providers_bp
from .routes.trucks import trucks_bp
from .routes.rates import rates_bp
from .routes.bills import bills_bp'''

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    app.register_blueprint(health_bp)
    app.register_blueprint(providers_bp)
    # app.register_blueprint(trucks_bp)
    # app.register_blueprint(rates_bp)
    # app.register_blueprint(bills_bp)

    return app