import os
import subprocess

REPO_PATH = os.environ["PROJECT_ROOT"]
REPO_URL = "git@github.com:ORG/REPO.git"

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
