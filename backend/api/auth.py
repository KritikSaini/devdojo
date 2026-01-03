from fastapi import APIRouter, HTTPException, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from schemas.schemas import Token, UserCreate, UserOut, UserUpdate, ForgotPasswordRequest, ResetPasswordRequest
from manager.auth_manager import create_user, get_user_by_email, update_user_profile, update_user_password
from services.security import get_current_user,create_access_token,create_refresh_token
from utils.password_utils import verify_password, hash_password
from datetime import datetime



from manager.auth_manager import (
    get_user_by_email,
    create_password_reset,
    get_password_reset,
    mark_token_used,
)
from utils.password_utils import (
    generate_reset_token,
    hash_reset_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    return await create_user(user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(
        access_token=create_access_token(user_id=user["id"], email=user["email"]),
        refresh_token=create_refresh_token(user_id=user["id"], email=user["email"]),
    )

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)

# --- NEW ENDPOINT ---
@router.put("/me", response_model=UserOut)
async def update_me(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates the profile of the currently authenticated user.
    """
    user_id = current_user["id"]
    updated_user = await update_user_profile(user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(**updated_user)






import os
from datetime import datetime
from fastapi import HTTPException
from manager.auth_manager import (
    get_user_by_email,
    create_password_reset,
    get_password_reset,
    mark_token_used,
    update_user_password
)

from utils.password_utils import (
    generate_reset_token,
    hash_reset_token,
    hash_password
)

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    user = await get_user_by_email(payload.email)

    # Prevent user enumeration
    if not user:
        return {"message": "If email exists, reset link sent"}

    token, token_hash = generate_reset_token()
    await create_password_reset(payload.email, token_hash)

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    # Replace later with SES / SMTP
    print(f"[RESET LINK] {reset_link}")

    return {"message": "If email exists, reset link sent"}

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    token_hash = hash_reset_token(payload.token)

    # 🔍 fetch reset token doc
    reset_doc = await get_password_reset(token_hash)
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    data = reset_doc["_source"]
    print("🔁 RESET TOKEN EMAIL (from password_resets):", data["email"])
    print("🔁 RESET TOKEN TYPE:", type(data["email"]))


    # 🔒 already used
    if data.get("used"):
        raise HTTPException(status_code=400, detail="Token already used")

    # ⏰ expired
    if datetime.utcnow() > datetime.fromisoformat(data["expires_at"]):
        raise HTTPException(status_code=400, detail="Token expired")

    # 🔐 update password
    hashed_pwd = hash_password(payload.new_password)
    await update_user_password(data["email"], hashed_pwd)

    # ✅ mark token as used
    await mark_token_used(reset_doc["_id"])

    return {"message": "Password reset successful"}



