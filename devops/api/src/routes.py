from __future__ import annotations
from datetime import datetime
from flask import Response, request

def register_routes(app):
    @app.route("/")
    def index():
        return "Hello World", 200