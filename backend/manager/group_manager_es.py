from fastapi import HTTPException
from elasticsearch import AsyncElasticsearch, NotFoundError
from uuid import uuid4
from datetime import datetime
from schemas.schemas import GroupCreate

# Use the async client, consistent with the rest of the application
es = AsyncElasticsearch("http://localhost:9200")
GROUP_INDEX = "groups"

async def create_group_es(group_data: GroupCreate, user_id: str) -> dict:
    """
    Creates a new group document in Elasticsearch.
    The creator is automatically added as the first member.
    """
    group_id = str(uuid4())
    doc = {
        "id": group_id,
        "name": group_data.name,
        "description": group_data.description,
        "created_by": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "members": [user_id]  # Creator auto-joins
    }
    await es.index(index=GROUP_INDEX, id=group_id, document=doc)
    return doc

async def list_groups_es() -> list[dict]:
    """
    Retrieves all groups from Elasticsearch. This version ensures the
    document ID is included in the returned data.
    """
    response = await es.search(index=GROUP_INDEX, query={"match_all": {}}, size=1000)
    
    groups_list = []
    for hit in response["hits"]["hits"]:
        group_data = hit["_source"]
        # --- FIX: Manually add the document's unique ID to the dictionary ---
        # The 'id' field in _source might be missing in older documents, 
        # but '_id' is always present in the hit metadata.
        group_data["id"] = hit["_id"]
        groups_list.append(group_data)
        
    return groups_list

async def get_group_es(group_id: str) -> dict | None:
    """
    Retrieves a single group by its ID.
    """
    try:
        response = await es.get(index=GROUP_INDEX, id=group_id)
        group_data = response["_source"]
        group_data["id"] = response["_id"] # Also add the ID here for consistency
        return group_data
    except NotFoundError:
        return None

async def join_group_es(group_id: str, user_id: str) -> dict:
    """
    Adds a user to a group's member list.
    """
    try:
        script = {
            "source": "if (!ctx._source.members.contains(params.user_id)) { ctx._source.members.add(params.user_id) }",
            "lang": "painless",
            "params": {"user_id": user_id}
        }
        await es.update(index=GROUP_INDEX, id=group_id, script=script)
        return {"message": "Successfully joined group"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Group not found")
    except Exception as e:
        print(f"Error joining group: {e}")
        raise HTTPException(status_code=500, detail="Could not join group.")

async def get_group_members_es(group_id: str) -> list[str]:
    """
    Retrieves the list of member IDs for a group.
    """
    group = await get_group_es(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group.get("members", [])