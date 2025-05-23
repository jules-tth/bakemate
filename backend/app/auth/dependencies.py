from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt # PyJWT was used in jwt.py, but jose is also common with FastAPI docs. Let's stick to PyJWT for consistency with jwt.py
from pydantic import ValidationError
from sqlmodel import Session

from uuid import UUID

from app.core.config import settings
from app.models.user import User
from app.models.token import TokenPayload # Using the one from models/token.py
from app.repositories.sqlite_adapter import get_session # Or your DB session getter
from app.services.user_service import UserService
from app.auth.jwt import decode_access_token # Using our existing decode function

# OAuth2PasswordBearer will point to the token URL
# This is the URL that the client will use to send the username and password
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)

async def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(reusable_oauth2)
) -> User:
    token_payload = decode_access_token(token)
    if not token_payload or not token_payload.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials - token invalid or expired",
        )
    
    user_service = UserService(session=session)
    user = await user_service.get_user_by_id(user_id=UUID(token_payload.sub))
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn\'t have enough privileges"
        )
    return current_user

