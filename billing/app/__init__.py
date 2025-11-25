from flask import Flask
from .config import Config
from .routes.health import health_bp

from .routes.provider import providers_bp
from .routes.truck import trucks_bp
from .routes.rates import rates_bp
from .routes.provider_ui import ui_provider_bp
from .routes.rates_ui import ui_rates_bp
from .routes.bills import bills_bp
from .routes.truck_ui import ui_truck_bp
from .routes.bills_ui import ui_bills_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(health_bp)
    app.register_blueprint(providers_bp)
    app.register_blueprint(bills_bp)
    app.register_blueprint(trucks_bp)
    app.register_blueprint(rates_bp)
    app.register_blueprint(ui_provider_bp)
    app.register_blueprint(ui_rates_bp)
    app.register_blueprint(ui_truck_bp)
    app.register_blueprint(ui_bills_bp)

    return app

