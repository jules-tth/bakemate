from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.user import User, UserCreate
from app.auth.security import get_password_hash, verify_password
from app.repositories.sqlite_adapter import SQLiteRepository # Or a generic repository factory

class UserService:
    def __init__(self, session: Session):
        # In a more complex setup, you might inject a repository factory
        # or specific repositories. For now, directly using SQLiteRepository.
        self.user_repo = SQLiteRepository(model=User) # type: ignore
        self.session = session # Pass session to repo methods if they don_t manage their own

    async def get_user_by_email(self, email: str) -> Optional[User]:
        # The SQLiteRepository get_by_attribute expects the session to be handled internally
        # or passed. Let_s assume it handles it or we pass it if needed.
        # For now, let_s use a direct session query for simplicity here, or adapt repo.
        statement = select(User).where(User.email == email)
        user = self.session.exec(statement).first()
        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        user = self.session.exec(statement).first()
        return user

    async def create_user(self, user_create: UserCreate) -> User:
        hashed_password = get_password_hash(user_create.password)
        # Create a dictionary for user creation, excluding the plain password
        user_data = user_create.model_dump(exclude={"password"})
        db_user = User(**user_data, hashed_password=hashed_password)
        
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    # Placeholder for email verification logic
    async def send_verification_email(self, email_to: str, user_id: UUID, token: str):
        # This would use SendGrid client to send an email with a verification link
        # Link would be something like: https://yourdomain.com/verify-email?token=<token>
        # The token would be a short-lived JWT or a one-time use token stored in DB
        print(f"Simulating sending verification email to {email_to} for user {user_id} with token {token}")
        # In a real app: call SendGrid service here
        pass

    async def verify_user_email(self, user_id: UUID) -> Optional[User]:
        user = await self.get_user_by_id(user_id=user_id)
        if user and not user.is_active: # Or a specific `is_verified` field
            user.is_active = True # Activate user upon email verification
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        return None

