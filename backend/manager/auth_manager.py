from elasticsearch import AsyncElasticsearch
from uuid import uuid4
from schemas.schemas import UserCreate, UserUpdate
from utils.password_utils import hash_password
from datetime import datetime
from datetime import datetime, timedelta
from utils.es_utils import es



USER_INDEX = "users"


# --- Create User ---
async def create_user(user: UserCreate) -> dict:
    user_id = str(uuid4())
    hashed_pw = hash_password(user.password)
    doc = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_pw,
        "github_username": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    await es.index(index=USER_INDEX, id=user_id, document=doc)
    return {"id": user_id, "username": user.username, "email": user.email}


# --- Get User by Email ---
async def get_user_by_email(email: str) -> dict | None:
    email = email.strip().lower()

    response = await es.search(index=USER_INDEX, query={"term": {"email": email}})

    hits = response["hits"]["hits"]
    return hits[0]["_source"] if hits else None


# --- Get User by ID ---
async def get_user_by_id(user_id: str) -> dict | None:
    try:
        response = await es.get(index=USER_INDEX, id=user_id)
        return response["_source"]
    except NotFoundError:
        return None


# --- Update User Profile ---
async def update_user_profile(user_id: str, user_update: UserUpdate) -> dict | None:
    script = {
        "source": "ctx._source.github_username = params.github_username",
        "lang": "painless",
        "params": {"github_username": user_update.github_username},
    }
    try:
        await es.update(index=USER_INDEX, id=user_id, script=script)
        updated_user = await get_user_by_id(user_id)
        return updated_user
    except NotFoundError:
        return None


# --- NEW: Delete User ---
async def delete_user_by_id(user_id: str) -> bool:
    """
    Deletes a user from Elasticsearch by their ID.
    Returns True if deletion is successful, False if user not found.
    """
    try:
        await es.delete(index=USER_INDEX, id=user_id)
        return True
    except NotFoundError:
        return False


async def get_user_by_github_username(github_username: str) -> dict | None:
    """
    Finds a user in our system based on their GitHub username.
    This is critical for the webhook to link a GitHub push to a Dojo user.
    """
    query = {"query": {"term": {"github_username.keyword": github_username}}}
    response = await es.search(index=USER_INDEX, body=query)
    hits = response["hits"]["hits"]
    return hits[0]["_source"] if hits else None


PASSWORD_RESET_INDEX = "password_resets"


async def create_password_reset(email: str, token_hash: str):
    await es.index(
        index=PASSWORD_RESET_INDEX,
        document={
            "email": email,
            "token_hash": token_hash,
            "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
            "used": False,
        },
    )


async def get_password_reset(token_hash):
    if not await es.indices.exists(index="password_resets"):
        return None

    res = await es.search(
        index="password_resets", body={"query": {"term": {"token_hash": token_hash}}}
    )

    hits = res.get("hits", {}).get("hits", [])
    return hits[0] if hits else None


async def mark_token_used(doc_id: str):
    await es.update(index=PASSWORD_RESET_INDEX, id=doc_id, doc={"used": True})


async def update_user_password(email: str, hashed_password: str):
    print("🔍 SEARCHING USER EMAIL:", email)
    print("🔍 EMAIL TYPE:", type(email))
    print("🔍 EMAIL LENGTH:", len(email))

    res = await es.search(index="users", query={"term": {"email": email}})

    if not res["hits"]["hits"]:
        raise Exception("User not found")

    user_id = res["hits"]["hits"][0]["_id"]

    await es.update(
        index="users",
        id=user_id,
        doc={"hashed_password": hashed_password},  # 🔑 THIS FIELD NAME MATTERS
    )

    return True
