import os
from github import Github, GithubException
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

g = Github(GITHUB_ACCESS_TOKEN) if GITHUB_ACCESS_TOKEN else None

def create_challenge_repository_and_invite(
    challenge_id: str,
    user_id: str,
    collaborator_username: str
) -> Optional[Dict[str, str]]:
    if not g or not WEBHOOK_URL or not WEBHOOK_SECRET:
        print("[ERROR] GitHub env vars TOKEN, URL, SECRET not configured.")
        return None

    repo_name = f"dojo-{challenge_id}-{user_id}"

    config = {
        "url": WEBHOOK_URL.rstrip("/"),
        "content_type": "json",
        "secret": WEBHOOK_SECRET
    }
    events = ["push", "pull_request", "issues"]

    try:
        auth_user = g.get_user()
        repo = auth_user.create_repo(
            name=repo_name,
            private=True,
            auto_init=True,
            description=f"Dojo submission repo for challenge {challenge_id}"
        )
        print(f"✅ Created repo: {repo.full_name}")
        repo.add_to_collaborators(collaborator_username, permission="push")
        print(f"🧑‍💻 Added collaborator: {collaborator_username}")

        repo.create_hook("web", config=config, events=events, active=True)
        print(f"🔔 Webhook created on {repo.full_name}")

        return {"repo_name": repo.full_name, "clone_url": repo.clone_url}

    except GithubException as e:
        if e.status == 422 and "name already exists" in str(e.data):
            print(f"[WARN] Repo exists: {repo_name}")
            try:
                existing_repo = g.get_repo(f"{auth_user.login}/{repo_name}")
                existing_repo.create_hook("web", config=config, events=events, active=True)
                print(f"🔔 Webhook ensured on existing repo {existing_repo.full_name}")
                return {"repo_name": existing_repo.full_name, "clone_url": existing_repo.clone_url}
            except GithubException as get_e:
                print(f"❌ Failed existing repo fetch: {get_e.data}")
        else:
            print(f"❌ GitHub API error: {e.data}")
        return None
