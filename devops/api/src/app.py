from flask import Flask
from routes import register_routes
from deploy import deploy
from monitor import start_monitoring



def create_app() -> Flask:
    app = Flask(__name__, static_folder="static")
    register_routes(app)
    start_monitoring()
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
    