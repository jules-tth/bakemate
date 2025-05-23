from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session # Assuming SQLite for now, can be made generic
from app.services.user_service import UserService
from app.models.user import UserCreate, UserRead
from app.models.token import Token
from app.auth.jwt import create_access_token
from app.auth.security import verify_password

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    *, 
    session: Session = Depends(get_session),
    user_in: UserCreate
):
    """    Create new user.
    """
    user_service = UserService(session=session)
    user = await user_service.get_user_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    new_user = await user_service.create_user(user_create=user_in)
    # Here you would typically trigger an email verification process
    # await send_verification_email(new_user.email, new_user.id) # Placeholder
    return new_user

@router.post("/login/access-token", response_model=Token)
async def login_for_access_token(
    response: Response,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Username is the email.
    """
    user_service = UserService(session=session)
    user = await user_service.authenticate_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token = create_access_token(
        subject=user.id # Using user.id as the subject for the token
    )
    
    # Set a secure cookie (optional, but good practice for web apps)
    # response.set_cookie(
    #     key=settings.SECURE_COOKIE_NAME,
    #     value=access_token,
    #     httponly=True,
    #     max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    #     expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    #     samesite="Lax", # or "Strict"
    #     secure=True, # True if served over HTTPS
    # )
    return {"access_token": access_token, "token_type": "bearer"}

# Placeholder for current_user dependency
# from app.auth.dependencies import get_current_active_user
# @router.get("/users/me", response_model=UserRead)
# async def read_users_me(current_user: UserRead = Depends(get_current_active_user)):
#     """
#     Test endpoint to get current user.
#     """
#     return current_user

