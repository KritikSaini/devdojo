from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

# ==================================
# User & Authentication Schemas
# ==================================
class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Schema for updating a user's profile. Only github_username is updatable for now."""
    github_username: str

class UserOut(BaseModel):
    """Public-facing user data."""
    id: str
    username: str
    email: EmailStr
    github_username: Optional[str] = None # <-- ADDED: So frontend can see it

class Token(BaseModel):
    """Schema for returning JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data decoded from a JWT token."""
    user_id: Optional[str]
    email: Optional[EmailStr]

# ==================================
# Group Schemas
# ==================================
class GroupCreate(BaseModel):
    """Schema for creating a new group."""
    name: str
    description: str

class GroupOut(GroupCreate):
    """Schema for returning group data, including its unique ID."""
    id: str # Changed from group_id for consistency
    created_by: str
    members: Optional[List[str]] = []


# ==================================
# Challenge Schemas
# ==================================
class ChallengeCreate(BaseModel):
    """Schema for the frontend to create a new challenge."""
    Topic: str
    difficulty: str
    group_id: str

class ChallengeOut(BaseModel):
    """Schema for returning a created challenge's data."""
    id: str
    Topic: str
    difficulty: str
    group_id: str
    created_by: str
    problem_statement: Optional[str] = None

# ==================================
# Submission Schemas
# ==================================
class SubmissionOut(BaseModel):
    """
    Schema for returning submission data. This reflects the fields
    created by the GitHub webhook.
    """
    id: str
    challenge_id: str
    user_id: str
    repo_name: str
    clone_url: str
    commit_hash: str
    status: str
    score: Optional[float] = None
    feedback: Optional[str] = None

# ==================================
# Leaderboard Schemas
# ==================================
class LeaderboardEntry(BaseModel):
    """Represents a single entry on a leaderboard."""
    user_id: str
    username: str
    score: float 

class GroupLeaderboardEntry(LeaderboardEntry):
    """Extends the leaderboard entry with a group_id."""
    group_id: str





class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str