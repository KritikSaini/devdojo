import os
import asyncio
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path
from elasticsearch import AsyncElasticsearch

# Assuming these are your actual import paths
from services.security import get_current_user
from schemas.schemas import ChallengeCreate, ChallengeOut
from services.dify_agents import (
    trigger_agent_1,
    trigger_agent_2_breakdown,
    trigger_agent_3_testcases,
)
from utils.es_utils import save_challenge, get_challenges_by_group
from services.sns_notify import notify_member_of_new_repo
from services.github_service import create_challenge_repository_and_invite
from manager.group_manager_es import get_group_members_es
from manager.auth_manager import get_user_by_id

# --- Configuration ---
CHALLENGE_INDEX = "challenges"
BREAKDOWN_INDEX = "breakdowns"
TESTCASE_INDEX = "testcases"
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

es = AsyncElasticsearch(ELASTICSEARCH_URL)
router = APIRouter(prefix="/challenges", tags=["Challenges"])

# --- Background Task ---
async def setup_challenge_repos_for_group(
    challenge_id: str,
    group_id: str,
    challenge_topic: str
):
    """
    Creates a unique, private GitHub repo for each member of a group.
    """
    print(f"🚀 Starting background task: Create repos for challenge {challenge_id}")
    
    member_ids = await get_group_members_es(group_id)
    if not member_ids:
        print(f"[WARN] No members found for group {group_id}.")
        return

    for user_id in member_ids:
        user = await get_user_by_id(user_id)
        if not user:
            print(f"[WARN] User {user_id} not found. Skipping.")
            continue

        email = user.get("email")
        github_username = user.get("github_username")

        if not email or not github_username:
            print(f"[WARN] User {user_id} missing email or GitHub username. Skipping.")
            continue

        print(f"Creating repo for challenge '{challenge_id}' for user '{github_username}'...")

        # Correctly call the service with structured IDs
        repo_details = create_challenge_repository_and_invite(
            challenge_id=challenge_id,
            user_id=user_id,
            collaborator_username=github_username
        )

        if not repo_details:
            print(f"❌ Repo creation failed for user {user_id}.")
            continue

        # Notify the user with details returned from the service
        notify_member_of_new_repo(
            email=email,
            challenge_title=challenge_topic,
            repo_name=repo_details["repo_name"],
            clone_url=repo_details["clone_url"]
        )
        await asyncio.sleep(2) # Avoid hitting API rate limits

    print(f"✅ Repo setup completed for challenge {challenge_id}")


@router.post("/", response_model=ChallengeOut, status_code=202)
async def create_challenge(
    challenge: ChallengeCreate,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    """
    Creates a challenge, generates content via agents, and schedules repo creation.
    """
    challenge_id = str(uuid4())
    doc = challenge.dict()
    doc["id"] = challenge_id
    doc["created_by"] = current_user["id"]

    # This part can take a long time. For a real application, consider a
    # proper job queue (like Celery) instead of awaiting here.
    try:
        print(f"[{challenge_id}] Triggering agents for topic: {challenge.Topic}")
        problem_statement = await trigger_agent_1(Topic=challenge.Topic, difficulty=challenge.difficulty, user_id=current_user["id"])
        doc["problem_statement"] = problem_statement.get("data", {}).get("outputs", {}).get("answer", "").strip()
        if not doc["problem_statement"]:
            raise ValueError("Agent 1 (Problem Statement) returned empty.")

        breakdown_result = await trigger_agent_2_breakdown(statement=doc["problem_statement"], user_id=current_user["id"])
        breakdown_text = breakdown_result.get("data", {}).get("outputs", {}).get("answer", {}).get("api", "")
        
        test_result = await trigger_agent_3_testcases(prompt=doc["problem_statement"], user_id=current_user["id"])
        test_cases_text = test_result.get("data", {}).get("outputs", {}).get("answer", {}).get("raw_text_from_previous_step", "")

        # Save all generated content
        await save_challenge(doc)
        await es.index(index=BREAKDOWN_INDEX, id=challenge_id, document={"challenge_id": challenge_id, "breakdown": breakdown_text})
        await es.index(index=TESTCASE_INDEX, id=challenge_id, document={"challenge_id": challenge_id, "testcases": test_cases_text})
        print(f"[{challenge_id}] ✅ Agent generation complete.")

    except Exception as e:
        print(f"❌ Exception during agent orchestration: {e}")
        raise HTTPException(status_code=503, detail=f"Agent failure: {e}")

    # Schedule the GitHub repo creation to run in the background
    background_tasks.add_task(
        setup_challenge_repos_for_group,
        challenge_id=challenge_id,
        group_id=challenge.group_id,
        challenge_topic=challenge.Topic,
    )

    print(f"[{challenge_id}] ✅ Background task for repo setup scheduled.")
    return ChallengeOut(**doc)


@router.get("/group/{group_id}", response_model=List[ChallengeOut])
async def get_challenge_history_for_group(
    group_id: str = Path(..., title="Group ID"),
    current_user=Depends(get_current_user)
):
    try:
        challenges = await get_challenges_by_group(group_id, size=5)
        return [ChallengeOut(**challenge) for challenge in challenges]
    except Exception as e:
        print(f"❌ Failed to get challenge history for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve challenge history.")
    


# --- NEW ENDPOINT for Challenge History ---
@router.get("/group/{group_id}", response_model=List[ChallengeOut])
async def get_challenge_history_for_group(
    group_id: str = Path(..., title="Group ID"),
    current_user=Depends(get_current_user)
):
    """
    Retrieves the last 5 challenges created for a specific group.
    """
    try:
        challenges = await get_challenges_by_group(group_id, size=5)
        return [ChallengeOut(**challenge) for challenge in challenges]
    except Exception as e:
        print(f"❌ Failed to get challenge history for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve challenge history.")
    

