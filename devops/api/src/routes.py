from __future__ import annotations
from datetime import datetime
from flask import Response, request , jsonify
from gitops import update_repo,verify_signature,change_to_project_root
from deploy import deploy,test_deploy
import hmac, hashlib, os, json


def register_routes(app):
    @app.route("/")
    def index():
        return "Hello World", 200
    
    @app.route("/webhook", methods=["POST"])
    @app.route("/webhook", methods=["POST"])
    def webhook():
        print("🔔 Webhook received")

        # --- Signature verification ---
        if not verify_signature(request):
            print("❌ Invalid signature")
            return jsonify({"error": "invalid signature"}), 403

        # --- Parse JSON ---
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "invalid json"}), 400

        # Extract branch: "refs/heads/master" → "master"
        ref = data.get("ref", "")
        branch = ref.replace("refs/heads/", "")

        print(f"📌 Branch pushed: {branch}")

        # we only support two branches
        if branch not in ["master", "development"]:
            print("➡️ Ignored: branch not allowed")
            return jsonify({"status": "ignored"}), 200

        print(f"🚀 Running CI/CD pipeline for: {branch}")

        # Change working directory
        change_to_project_root()

        # Update repo
        try:
            update_repo(branch)
        except Exception as e:
            print(e)
            return jsonify({"status": "repo update failed"}), 500

        # Run tests
        if not test_deploy(branch):
            return jsonify({"status": "tests failed"}), 400

        # Deploy if tests pass
        if deploy(branch):
            return jsonify({"status": "deployed"}), 200
        else:
            return jsonify({"status": "deploy failed"}), 500