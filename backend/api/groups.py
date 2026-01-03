from fastapi import APIRouter, Depends, HTTPException
from typing import List
from fastapi import BackgroundTasks
from schemas.schemas import GroupCreate, GroupOut
from services.sns_notify import notify_user_joined_group
from services.security import get_current_user
from manager.group_manager_es import (
    create_group_es,
    list_groups_es,
    get_group_es,
    join_group_es,
    get_group_members_es
)

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.post("/", response_model=GroupOut)
async def create_group(
    group: GroupCreate,
    current_user=Depends(get_current_user)
):
    group_data = await create_group_es(group, current_user["id"])
    # Solution: only pass **group_data, don't use both id=... and **group_data
    return GroupOut(**group_data)

@router.get("/", response_model=List[GroupOut])
async def list_groups():
    groups = await list_groups_es()
    return [GroupOut(**g) for g in groups]

@router.get("/{group_id}", response_model=GroupOut)
async def get_group(group_id: str):
    group_data = await get_group_es(group_id)
    if not group_data:
        raise HTTPException(status_code=404, detail="Group not found")
    return GroupOut(**group_data)

@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    group_data = await join_group_es(group_id, current_user["id"])
    user_email = current_user.get("email")
    group_name = group_data.get("name", "Unnamed Group")

    if user_email:
        background_tasks.add_task(notify_user_joined_group, user_email, group_name)
    else:
        print(f"[WARN] No email for user {current_user['id']}, skipping notification.")

    return group_data

@router.get("/{group_id}/members")
async def get_group_members(group_id: str):
    members = await get_group_members_es(group_id)
    return {"group_id": group_id, "members": members}
