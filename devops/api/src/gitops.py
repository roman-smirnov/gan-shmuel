import os
import subprocess

REPO_PATH = os.environ["PROJECT_ROOT"]
REPO_URL = "git@github.com:ORG/REPO.git"
import hmac, hashlib, os
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")  # the secret you set in GitHub

def repo_exists() -> bool:
    """Check if the repo folder already has a .git directory."""
    return os.path.isdir(os.path.join(REPO_PATH, ".git"))


def git_clone():
    """Clone the repository fresh."""
    print("📥 Cloning repository...")
    subprocess.run(["git", "clone", REPO_URL, REPO_PATH], check=True)


def git_pull(branch):
    try:
        print(f"🔄 Updating branch: {branch}")

        # Fetch latest from remote
        subprocess.run(["git", "-C", REPO_PATH, "fetch", "--all"], check=True)

        # Checkout the correct branch
        subprocess.run(["git", "-C", REPO_PATH, "checkout", branch], check=True)

        # Reset that branch to its remote
        subprocess.run(["git", "-C", REPO_PATH, "reset", "--hard", f"origin/{branch}"], check=True)

        print(f"✅ Branch {branch} is now up to date with origin/{branch}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git pull failed for {branch}: {e}")

def update_repo(branch):
    """Pull repo if exists, otherwise clone it."""
    if repo_exists():
        print("Repo exists → pulling latest changes...")
        try:
            git_pull(branch)
        except Exception as e:
            print(f"⚠️ Pull failed: {e}. Recloning...")
            git_clone()
            git_pull(branch)
    else:
        print("Repo missing → full clone...")
        git_clone()
        git_pull(branch)


def change_to_project_root():
    """Change working directory to the path defined in PROJECT_ROOT env variable."""
    project_root = os.environ.get("PROJECT_ROOT")

    if not project_root:
        raise RuntimeError("❌ PROJECT_ROOT environment variable is not set")

    try:
        os.chdir(project_root)
        print(f"📂 Changed working directory to: {project_root}")
        print(f"📌 Current CWD: {os.getcwd()}")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to change directory: {e}")
    

    

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

