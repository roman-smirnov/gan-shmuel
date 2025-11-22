from __future__ import annotations
from datetime import datetime
from flask import Response, request , jsonify
from gitops import update_repo
from deploy import deploy


def register_routes(app):
    @app.route("/")
    def index():
        return "Hello World", 200
    
    @app.route("/webhook", methods=["POST"])
    def webhook():
        print("🔔 Webhook received")
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "invalid json"}), 400
        

        # check if master
        ref = data.get("ref")
        if ref != "refs/heads/master":
            return jsonify({"status": "ignored (not master)"}), 200

        # pull code
        update_repo()

        # deploy containers
        deploy()

        return jsonify({"status": "deployed"}), 200