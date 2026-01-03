import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from schemas.schemas import TokenData
# DO NOT import from manager.auth_manager at the top level to avoid circular imports.

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*7
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Used by Swagger UI's "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(user_id: str, email: str) -> str:
    return create_token(
        {"sub": user_id, "user_id": user_id, "email": email},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

def create_refresh_token(user_id: str, email: str) -> str:
    return create_token(
        {"sub": user_id, "user_id": user_id, "email": email},
        timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
    )

def decode_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            user_id=payload.get("user_id"),
            email=payload.get("email"),
        )
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodes the JWT token, validates it, and fetches the current user.
    """
    # --- FIX: Import is moved inside the function to break the circular dependency ---
    from manager.auth_manager import get_user_by_email

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_token(token)
    if not token_data or not token_data.email:
        raise credentials_exception

    user = await get_user_by_email(token_data.email)
    if not user:
        raise credentials_exception

    # --- FIX: Return the entire user document from the manager ---
    # This ensures that other parts of the app (like api/challenges.py)
    # can access the user's "id" with the correct key.
    return user