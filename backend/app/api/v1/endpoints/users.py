from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from uuid import UUID
from datetime import timedelta

from app.repositories.sqlite_adapter import get_session # Or your DB session getter
from app.services.user_service import UserService
from app.models.user import User, UserRead
from app.auth.dependencies import get_current_active_user, get_current_active_superuser
from app.auth.jwt import create_access_token, decode_access_token # For email verification token
from app.core.config import settings
# from app.services.email_service import send_email_async # Placeholder for SendGrid integration

router = APIRouter()

@router.post("/verify-email-request", status_code=status.HTTP_202_ACCEPTED)
async def request_email_verification(
    current_user: UserRead = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Endpoint for a logged-in user to request a new email verification link.
    """
    if current_user.is_active: # Assuming is_active means verified for now
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified."
        )

    # Generate a short-lived token for email verification
    # This token will contain the user_id
    verification_token = create_access_token(subject=current_user.id, expires_delta=timedelta(hours=24))
    verification_link = f"{settings.API_V1_STR}/auth/verify-email/?token={verification_token}" # Adjust base URL as needed
    
    # Placeholder for sending email
    # await send_email_async(
    #     email_to=current_user.email,
    #     subject_template="Verify Your Email for BakeMate",
    #     html_template_name="email_verification.html",
    #     environment={
    #         "project_name": settings.PROJECT_NAME,
    #         "username": current_user.email, # Or a display name if available
    #         "verification_link": verification_link
    #     }
    # )
    print(f"SIMULATING: Verification email sent to {current_user.email} with link: {verification_link}")
    return {"msg": "Verification email sent. Please check your inbox."}

@router.get("/verify-email/", status_code=status.HTTP_200_OK)
async def verify_email(
    token: str = Query(...),
    session: Session = Depends(get_session)
):
    """
    Endpoint to handle email verification from the link sent to the user.
    """
    token_payload = decode_access_token(token)
    if not token_payload or not token_payload.sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token."
        )
    
    user_id_to_verify = UUID(token_payload.sub)
    user_service = UserService(session=session)
    user = await user_service.verify_user_email(user_id=user_id_to_verify)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token or user already verified/not found."
        )
    
    return {"msg": "Email verified successfully. You can now login."}

# Example of a protected route requiring an active (verified) user
@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: UserRead = Depends(get_current_active_user)):
    """
    Test endpoint to get current user, requires active (verified) status.
    """
    return current_user

# Example of a superuser protected route
@router.get("/users/all", response_model=list[UserRead], dependencies=[Depends(get_current_active_superuser)])
async def read_all_users(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all users. Only accessible by superusers.
    """
    # This is a simplified example. In a real app, you would use a service method.
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return users

