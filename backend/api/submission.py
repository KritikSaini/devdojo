from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import AsyncElasticsearch
from services.security import get_current_user
from schemas.schemas import SubmissionOut
from utils.es_utils import get_submission_by_id

SUBMISSION_INDEX = "submissions"
es = AsyncElasticsearch("http://localhost:9200")
router = APIRouter(prefix="/submissions", tags=["Submissions"])

@router.get("/", response_model=list[SubmissionOut])
async def get_my_submissions(user=Depends(get_current_user)):
    """
    Gets all submissions for the currently authenticated user from Elasticsearch.
    """
    # --- FIX: Added a query to filter by the current user's ID ---
    # Note: The 'user_id' in the submission doc is the GitHub username.
    # We assume the JWT's 'username' field holds this value.
    user_github_username = user.get("username")
    
    query = {
        "term": {
            "user_id.keyword": user_github_username
        }
    }
    
    res = await es.search(index=SUBMISSION_INDEX, query=query, size=100)
    return [SubmissionOut(**hit["_source"]) for hit in res["hits"]["hits"]]


@router.get("/{submission_id}", response_model=SubmissionOut)
async def get_submission(submission_id: str, user=Depends(get_current_user)):
    """
    Gets a specific submission by its ID.
    (Optionally, you could add a check here to ensure the user owns this submission)
    """
    res = await get_submission_by_id(submission_id)
    if not res:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Optional security check:
    # if res.get("user_id") != user.get("username"):
    #     raise HTTPException(status_code=403, detail="Not authorized to view this submission")

    return SubmissionOut(**res)