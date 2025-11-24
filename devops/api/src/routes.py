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
    def webhook():
            print("🔔 Webhook received")

            # --- Step 1: Verify GitHub signature (important for security) ---
            #if not verify_signature(request):
             #   print("❌ Invalid signature - rejected")
              #  return jsonify({"error": "invalid signature"}), 403
            #print("✅ Signature verified")

            # --- Step 2: Parse JSON ---
            data = request.get_json(silent=True)
            if not data:
                return jsonify({"error": "invalid json"}), 400

            # --- Step 3: Extract required fields ---
            ref = data.get("ref")                       # branch
            pusher = data.get("pusher", {}).get("name") # person who pushed
            repo_url = data.get("repository", {}).get("ssh_url")  # optional
            commit_sha = data.get("after")              # optional

            print(f"📌 Branch: {ref}")
            print(f"👤 Pusher: {pusher}")
            print(f"🔗 Repo URL: {repo_url}")
            print(f"🔑 Commit SHA: {commit_sha}")

            # --- Step 4: Only run CI on master ---
            if ref != "refs/heads/master":
                print("➡️ Ignored: not master")
                #return jsonify({"status": "ignored (not master)"}), 200

            print("🚀 Running CI for master branch...")
            change_to_project_root()
            update_repo()  

            #if test_deploy():
             #   print("All tests passed — deploying production…")
            deploy_status=deploy()
                ##mailing logic here
            #else:
             #   print("Tests failed — aborting deployment.")
                #mailing logic here
            if not deploy_status:
                print("❌ Production deploy failed.")
                exit(1)

            print("🎉 Deployment completed successfully!")
            return jsonify({"status": "deployed"}), 200
