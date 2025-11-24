import os
import subprocess

REPO_PATH = os.environ["PROJECT_ROOT"]
REPO_URL = "git@github.com:ORG/REPO.git"
import hmac, hashlib, os
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")  # the secret you set in GitHub

def repo_exists() -> bool:
    return os.path.isdir(os.path.join(REPO_PATH, ".git"))

def git_clone():
    subprocess.run(["git", "clone", REPO_URL, REPO_PATH], check=True)

def git_pull():
    subprocess.run(["git", "-C", REPO_PATH, "fetch", "--all"], check=True)
    subprocess.run(["git", "-C", REPO_PATH, "checkout", "master"], check=True)
    subprocess.run(["git", "-C", REPO_PATH, "reset", "--hard", "origin/master"], check=True)

def update_repo():
    if repo_exists():
        print("Repo exists → pulling...")
        git_pull()
    else:
        print("Repo missing → cloning...")
        git_clone()


# --- Signature verification helper ---
def verify_signature(request):
    """Validate X-Hub-Signature-256 header using WEBHOOK_SECRET."""
    if not WEBHOOK_SECRET:
        return True  # no secret set → skip verification

    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return False

    sha_name, signature_hash = signature.split("=")
    if sha_name != "sha256":
        return False

    mac = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=request.data,
        digestmod=hashlib.sha256
    )

    return hmac.compare_digest(mac.hexdigest(), signature_hash)

