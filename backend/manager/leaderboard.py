from typing import List
from collections import defaultdict
from schemas.schemas import LeaderboardEntry, GroupLeaderboardEntry
from utils.es_utils import get_leaderboard


async def get_global_leaderboard_es() -> List[LeaderboardEntry]:
    """
    Calculates the global leaderboard by aggregating user score across all groups.
    """
    all_entries = await get_leaderboard(group_id=None)

    user_score_aggregator = defaultdict(lambda: {"score": 0.0, "username": "Unknown"})

    for entry in all_entries:
        user_id = entry.get("user_id")
        if user_id:
            user_score_aggregator[user_id]["score"] += entry.get("score", 0.0)
            if user_score_aggregator[user_id]["username"] == "Unknown":
                user_score_aggregator[user_id]["username"] = entry.get("username", "Unknown")

    global_leaderboard = [
        LeaderboardEntry(
            user_id=user_id,
            username=data["username"],
            score=data["score"]
        )
        for user_id, data in user_score_aggregator.items()
    ]

    return sorted(global_leaderboard, key=lambda x: x.score, reverse=True)


async def get_group_leaderboard_es(group_id: str) -> List[GroupLeaderboardEntry]:
    """
    Fetches the leaderboard for a specific group.
    """
    leaderboard = await get_leaderboard(group_id=group_id)

    group_leaderboard = [
        GroupLeaderboardEntry(
            user_id=entry["user_id"],
            username=entry.get("username", "Unknown"),
            score=entry.get("score", 0.0),
            group_id=group_id
        )
        for entry in leaderboard
    ]

    return sorted(group_leaderboard, key=lambda x: x.score, reverse=True)
