import os
from typing import Dict, List
from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.exceptions import RequestError
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
CHALLENGE_INDEX = "challenges"
SUBMISSION_INDEX = "submissions"
LEADERBOARD_INDEX = "leaderboard"

# --- Elasticsearch Client Initialization ---
es = AsyncElasticsearch(ES_HOST)


# --- Index Initialization ---
async def init_indices():
    """Ensures all indices exist with proper mappings."""
    # Leaderboard index with explicit mapping
    if not await es.indices.exists(index=LEADERBOARD_INDEX):
        await es.indices.create(
            index=LEADERBOARD_INDEX,
            body={
                "mappings": {
                    "properties": {
                        "user_id": {"type": "keyword"},
                        "group_id": {"type": "keyword"},
                        "username": {"type": "text"},
                        "xp": {"type": "integer"}
                    }
                }
            }
        )


# --- Challenge Functions ---
async def save_challenge(challenge: Dict) -> str:
    """Saves a challenge document to Elasticsearch."""
    challenge_id = challenge["id"]
    res = await es.index(index=CHALLENGE_INDEX, id=challenge_id, document=challenge)
    print("Challenge save response:", res)
    return res["_id"]


async def get_challenge_by_id(challenge_id: str) -> Dict | None:
    """Retrieves a challenge document by its ID."""
    try:
        res = await es.get(index=CHALLENGE_INDEX, id=challenge_id)
        return res.get("_source")
    except NotFoundError:
        return None


# --- Submission Functions ---
async def save_submission(submission: Dict) -> str:
    """Saves a submission document to Elasticsearch."""
    res = await es.index(index=SUBMISSION_INDEX, document=submission)
    return res["_id"]


async def get_submission_by_id(submission_id: str) -> Dict | None:
    """Retrieves a submission document by its ID."""
    try:
        res = await es.get(index=SUBMISSION_INDEX, id=submission_id)
        return res.get("_source")
    except NotFoundError:
        return None


# --- Leaderboard Functions ---
async def update_leaderboard_xp(user_id: str, challenge_id: str, xp_to_add: int, username: str, score: float, feedback: str):
    """
    Updates a user's XP on the leaderboard for a specific challenge's group.
    Performs an upsert (update if exists, insert if not).
    """
    if not user_id:
        print("[WARN] Cannot update leaderboard for an unknown user.")
        return

    try:
        challenge_doc = await es.get(index=CHALLENGE_INDEX, id=challenge_id)
        group_id = challenge_doc["_source"].get("group_id")
    except NotFoundError:
        print(f"[ERROR] Cannot update leaderboard: Challenge {challenge_id} not found.")
        return

    if not group_id:
        print(f"[WARN] Challenge {challenge_id} has no group_id. Skipping leaderboard update.")
        return

    doc_id = f"{group_id}_{user_id}"

    script = {
        "source": "ctx._source.xp += params.xp",
        "lang": "painless",
        "params": {"xp": xp_to_add}
    }

    upsert_doc = {
        "user_id": user_id,
        "group_id": group_id,
        "username": username,
        "xp": xp_to_add,  # ✅ use 'xp' instead of 'score'
        "score": score,
        "feedback": feedback,
    }

    try:
        await es.update(index=LEADERBOARD_INDEX, id=doc_id, script=script, upsert=upsert_doc)
    except RequestError as e:
        print("[ERROR] Failed to update leaderboard entry:", e)



async def get_leaderboard(group_id: str | None) -> List[dict]:
    """
    Fetches leaderboard entries from Elasticsearch.
    Sorted by XP in descending order.
    """
    query = {"match": {"group_id": group_id}} if group_id else {"match_all": {}}

    try:
        res = await es.search(
            index=LEADERBOARD_INDEX,
            query=query,
            size=100,
            sort=[{"xp": {"order": "desc"}}]
        )
        print(f"here we have response froom es: {res}")
        return [hit["_source"] for hit in res["hits"]["hits"]]
    except RequestError as e:
        print("[ERROR] Failed to fetch leaderboard:", e)
        return []

async def get_challenges_by_group(group_id: str, size: int = 5) -> List[Dict]:
    """
    Fetches the most recent challenges for a specific group, sorted by creation date.
    Uses the correct 'term' query for a 'keyword' field.
    """
    query = {
        "term": {
            # The field is already a keyword, so we don't need the .keyword suffix
            "group_id": group_id
        }
    }
    sort = [
        {"created_at": {"order": "desc"}}
    ]
    res = await es.search(index=CHALLENGE_INDEX, query=query, sort=sort, size=size)
    return [hit["_source"] for hit in res["hits"]["hits"]]