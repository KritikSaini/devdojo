import os
from typing import Dict, List
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import RequestError, NotFoundError

# Load env early (local support)
load_dotenv()

# --- Environment ---
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")

if not ELASTICSEARCH_URL or not ELASTICSEARCH_API_KEY:
    raise RuntimeError("Elasticsearch config missing")

# --- Async Elasticsearch client ---
es = AsyncElasticsearch(
    ELASTICSEARCH_URL,
    api_key=ELASTICSEARCH_API_KEY,
    request_timeout=10
)

# --- Index names ---
CHALLENGE_INDEX = "challenges"
SUBMISSION_INDEX = "submissions"
LEADERBOARD_INDEX = "leaderboard"


# --- Index Initialization ---
async def init_indices():
    if not await es.indices.exists(index=LEADERBOARD_INDEX):
        await es.indices.create(
            index=LEADERBOARD_INDEX,
            body={
                "mappings": {
                    "properties": {
                        "user_id": {"type": "keyword"},
                        "group_id": {"type": "keyword"},
                        "username": {"type": "text"},
                        "xp": {"type": "integer"},
                        "score": {"type": "float"},
                        "feedback": {"type": "text"},
                    }
                }
            }
        )


# --- Challenge ---
async def save_challenge(challenge: Dict) -> str:
    res = await es.index(
        index=CHALLENGE_INDEX,
        id=challenge["id"],
        document=challenge
    )
    return res["_id"]


async def get_challenge_by_id(challenge_id: str) -> Dict | None:
    try:
        res = await es.get(index=CHALLENGE_INDEX, id=challenge_id)
        return res["_source"]
    except NotFoundError:
        return None


async def get_challenges_by_group(group_id: str, size: int = 5) -> List[Dict]:
    res = await es.search(
        index=CHALLENGE_INDEX,
        query={"term": {"group_id": group_id}},
        sort=[{"created_at": {"order": "desc"}}],
        size=size
    )
    return [hit["_source"] for hit in res["hits"]["hits"]]


# --- Submissions ---
async def save_submission(submission: Dict) -> str:
    res = await es.index(index=SUBMISSION_INDEX, document=submission)
    return res["_id"]


async def get_submission_by_id(submission_id: str) -> Dict | None:
    try:
        res = await es.get(index=SUBMISSION_INDEX, id=submission_id)
        return res["_source"]
    except NotFoundError:
        return None


# --- Leaderboard ---
async def update_leaderboard_xp(
    user_id: str,
    challenge_id: str,
    xp_to_add: int,
    username: str,
    score: float,
    feedback: str
):
    if not user_id:
        return

    try:
        challenge_doc = await es.get(index=CHALLENGE_INDEX, id=challenge_id)
        group_id = challenge_doc["_source"].get("group_id")
    except NotFoundError:
        return

    if not group_id:
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
        "xp": xp_to_add,
        "score": score,
        "feedback": feedback,
    }

    try:
        await es.update(
            index=LEADERBOARD_INDEX,
            id=doc_id,
            script=script,
            upsert=upsert_doc
        )
    except RequestError as e:
        print("[ERROR] Leaderboard update failed:", e)


async def get_leaderboard(group_id: str | None) -> List[dict]:
    query = {"term": {"group_id": group_id}} if group_id else {"match_all": {}}

    try:
        res = await es.search(
            index=LEADERBOARD_INDEX,
            query=query,
            size=100,
            sort=[{"xp": {"order": "desc"}}]
        )
        return [hit["_source"] for hit in res["hits"]["hits"]]
    except RequestError as e:
        print("[ERROR] Fetch leaderboard failed:", e)
        return []
