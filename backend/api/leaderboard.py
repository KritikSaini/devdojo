from fastapi import APIRouter, Depends
from typing import List
from services.security import get_current_user
from schemas.schemas import LeaderboardEntry, GroupLeaderboardEntry
from manager.leaderboard import (
    get_global_leaderboard_es,
    get_group_leaderboard_es,
)

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


# ---------------- Global Leaderboard ----------------
@router.get("/global", response_model=List[LeaderboardEntry])
async def get_global_leaderboard(current_user=Depends(get_current_user)):
    return await get_global_leaderboard_es()


# ---------------- Group Leaderboard ----------------
@router.get("/group/{group_id}", response_model=List[GroupLeaderboardEntry])
async def get_group_leaderboard(group_id: str, current_user=Depends(get_current_user)):
    return await get_group_leaderboard_es(group_id)
