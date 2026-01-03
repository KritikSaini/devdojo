import os
import hmac
import hashlib
import traceback
import json
import re
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
from elasticsearch import AsyncElasticsearch

from manager.testcase_manager import get_testcases_by_challenge
from services.dify_agents import trigger_agent_4_evaluation
from utils.es_utils import update_leaderboard_xp
from utils.git_utils import get_code_from_repo  # Now synchronous
from dotenv import load_dotenv
from manager.auth_manager import get_user_by_id

# ✅ Safe runtime check instead of crashing assertion

load_dotenv()

router = APIRouter(prefix="/webhook", tags=["GitHub Webhook"])
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dummysecret")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
es = AsyncElasticsearch(ELASTICSEARCH_URL)
SUBMISSION_INDEX = "submissions"


def verify_signature(payload_body: bytes, signature: str) -> bool:
    if not signature:
        print("❌ No signature header provided")
        return False
    try:
        sha_name, received_sig = signature.split("=")
        if sha_name != "sha256":
            print(f"❌ Unsupported signature type: {sha_name}")
            return False
    except ValueError:
        print("❌ Malformed signature")
        return False

    expected_mac = hmac.new(WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha256).hexdigest()
    print(f"🔐 Expected signature: {expected_mac}")
    print(f"📩 Received signature: {received_sig}")
    return hmac.compare_digest(expected_mac, received_sig)


async def process_submission(submission_doc: dict, testcases_str: str):
    submission_id = submission_doc["id"]
    print(f"🚀 Starting evaluation for submission: {submission_id}")
    final_status = {"status": "error", "score": 0.0}

    try:
        print(f"📥 Cloning repo: {submission_doc['clone_url']} at commit {submission_doc['commit_hash']}")
        user_code_str = get_code_from_repo(
            clone_url=submission_doc["clone_url"],
            commit_hash=submission_doc["commit_hash"]
        )
        print(f"✅ Repo cloned")

        print(f"🤖 Triggering Agent 4 evaluation...")
        result = await trigger_agent_4_evaluation(
            user_code=user_code_str,
            test_cases=testcases_str,
            user_id=submission_doc["user_id"]
        )
        print(f"✅ Agent 4 triggered")
        print("📦 Raw Agent 4 Answer:")
        print(json.dumps(result.get("data", {}).get("outputs", {}), indent=2))

        outputs = result.get("data", {}).get("outputs", {})
        score = float(outputs.get("score", 0.0))
        feedback = outputs.get("feedback", "")

        final_status = {
            "status": "completed",
            "score": score,
            "feedback": feedback
        }

        print(f"✅ Evaluation complete for {submission_id}. Score: {score}")

        if score > 0:
            await update_leaderboard_xp(
                user_id=submission_doc["user_id"],
                challenge_id=submission_doc["challenge_id"],
                xp_to_add=submission_doc.get("xp", 0),
                username=submission_doc.get("username", submission_doc["user_id"]),
                score=score,
                feedback=feedback
            )

    except Exception as e:
        print(f"❌ Evaluation process failed for {submission_id}: {e}")
        print(traceback.format_exc())

    update_body = {
        "doc": {
            **final_status,
            "processed_at": datetime.now(timezone.utc)
        }
    }
    await es.update(index=SUBMISSION_INDEX, id=submission_id, body=update_body)
    print(f"✅ Submission saved to Elasticsearch with status: {final_status['status']}")


@router.post("/")
@router.post("")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None)
):
    body = await request.body()
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")

    print("✅ Webhook received from GitHub")
    payload = json.loads(body)

    if 'pusher' not in payload:
        print("⚠ Ignored non-push event")
        return {"status": "ignored", "reason": "Not a push event."}

    head_commit = payload.get("head_commit", {})
    changed_files = head_commit.get("modified", []) + head_commit.get("added", [])
    changed_files = [f.lower() for f in changed_files]

    if changed_files and all(f == "readme.md" for f in changed_files):
        print("⚠ Skipping evaluation: only README.md was changed.")
        return {"status": "ignored", "reason": "README-only change."}

    repo_name = payload.get("repository", {}).get("full_name")
    print(f"📁 Repo Name: {repo_name}")

    match = re.search(r"/dojo-([a-f0-9\-]{36})-([^/]+)", repo_name)
    if not match:
        print(f"⚠ Repo name does not match expected format: {repo_name}")
        return {"status": "ignored", "reason": f"Repo name '{repo_name}' does not match expected format."}

    challenge_id = match.group(1)
    github_user_id = match.group(2)
    print(f"🧠 Challenge ID: {challenge_id}, GitHub User: {github_user_id}")

    user_doc = await get_user_by_id(github_user_id)
    if not user_doc:
        print(f"❌ User not found in system for GitHub username: {github_user_id}")
        raise HTTPException(status_code=404, detail=f"User '{github_user_id}' not found in DOJO system.")

    actual_user_id_for_db = user_doc.get("id", github_user_id)
    actual_username_for_display = user_doc.get("username", github_user_id)

    if payload.get("deleted", False):
        print("⚠ Ignoring branch deletion event")
        return {"status": "ignored", "reason": "Branch deletion push."}

    query = {
        "bool": {
            "must": [
                {"term": {"challenge_id": challenge_id}},
                {"term": {"user_id": actual_user_id_for_db}},
                {"term": {"status": "completed"}}
            ]
        }
    }
    existing = await es.search(index=SUBMISSION_INDEX, query=query, size=2)
    if existing["hits"]["total"]["value"] > 2:
        print(f"⚠ Duplicate submission blocked for user={actual_user_id_for_db}, challenge={challenge_id}")
        return {"status": "ignored", "reason": "Already evaluated."}

    submission_id = str(uuid4())
    doc = {
        "id": submission_id,
        "challenge_id": challenge_id,
        "user_id": actual_user_id_for_db,
        "username": actual_username_for_display,
        "repo_name": repo_name,
        "clone_url": payload["repository"]["clone_url"],
        "commit_hash": payload["after"],
        "commit_message": head_commit.get("message", ""),
        "source": "webhook",
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }

    testcases_str = await get_testcases_by_challenge(challenge_id)
    await es.index(index=SUBMISSION_INDEX, id=submission_id, document=doc)
    background_tasks.add_task(process_submission, doc, testcases_str)
    print(f"✅ Submission created and evaluation started for {submission_id}")
    return {"status": "submitted", "submission_id": submission_id}
