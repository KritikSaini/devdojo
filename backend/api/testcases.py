from fastapi import APIRouter, Depends, HTTPException
from manager.testcase_manager import get_testcases_by_challenge
from services.security import get_current_user
import json

router = APIRouter(prefix="/testcases", tags=["TestCases"])

@router.get("/{challenge_id}", response_model=dict)
async def get_testcases(
    challenge_id: str,
    user=Depends(get_current_user)
):
    """
    Retrieves the test cases for a given challenge ID.
    The test cases are stored as a single string, which may be JSON.
    """
    testcases_str = await get_testcases_by_challenge(challenge_id)
    
    if not testcases_str:
        raise HTTPException(status_code=404, detail="Test cases not found for this challenge.")

    # Try to parse the string as JSON, but fall back to returning the raw string
    # if it's not valid JSON. This makes the endpoint robust.
    try:
        parsed_testcases = json.loads(testcases_str)
        return {
            "challenge_id": challenge_id,
            "testcases": parsed_testcases
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "challenge_id": challenge_id,
            "testcases": testcases_str # Return as raw text
        }
