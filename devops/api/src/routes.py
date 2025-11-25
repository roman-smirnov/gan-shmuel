from __future__ import annotations
from datetime import datetime
from flask import Response, request , jsonify
from gitops import update_repo,verify_signature,change_to_project_root
from deploy import deploy,test_deploy,test_shutdown
import hmac, hashlib, os, json
from emails import send_email


def register_routes(app):
    @app.route("/")
    def index():
        return "Hello World", 200
    
    @app.route("/webhook", methods=["POST"])
    def webhook():
        print("🔔 Webhook received")

        # --- Signature verification ---
        # if not verify_signature(request):
        #     print("❌ Invalid signature")
        #     return jsonify({"error": "invalid signature"}), 403

        # --- Parse JSON ---
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "invalid json"}), 400
        repo_owner_email = (
            data.get("repository", {})
                .get("owner", {})
                .get("email", "not-provided")
        )

        pusher_email = (
            data.get("pusher", {})
                .get("email", "not-provided")
        )
        author_email = (
            data.get("head_commit", {})
                .get("author", {})
                .get("email", "")
        )


        print(f"📧 Repo owner: {repo_owner_email}"
              f", Pusher: {pusher_email}")

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
        # Run tests for any branch
        if not test_deploy():
            if author_email:
                send_email("TEST FAILED", "",[author_email])
            test_shutdown()
            return jsonify({"status": "tests failed"}), 400
        
        test_shutdown()
        if author_email:
            send_email("TEST PASSED", "",[author_email])
        
        # Deploy only if master
        if branch == "master":
            print("🚀 Master branch pushed — deploying...")
            if deploy():
                if author_email:
                    send_email("DEPLOYED TO PRODUCTION", "",[author_email])
                return jsonify({"status": "deployed"}), 200
            else:
                if author_email:
                    send_email("DEPLOYED TO PRODUCTION FAILED", "",[author_email])
                return jsonify({"status": "deploy failed"}), 500
        else:
            print("ℹ️ Development branch pushed — tests passed but no deployment.")
            return jsonify({"status": "tests passed (no deployment)"}), 200
