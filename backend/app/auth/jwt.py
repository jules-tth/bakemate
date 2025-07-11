from datetime import datetime, timedelta, timezone
from typing import Optional, Any

import jwt
from pydantic import BaseModel, ValidationError

from app.core.config import settings


class TokenPayload(BaseModel):
    sub: Optional[Any] = None  # Subject (usually user ID or email)
    exp: Optional[datetime] = None
    # Add any other custom claims you need
    # e.g., tenant_id: Optional[str] = None


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = TokenPayload(sub=str(subject), exp=expire).model_dump()
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """Decodes a JWT access token and returns its payload."""
    try:
        payload_dict = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        # Manually add timezone info if exp is a naive datetime from jwt.decode
        if "exp" in payload_dict and isinstance(payload_dict["exp"], int):
            payload_dict["exp"] = datetime.fromtimestamp(
                payload_dict["exp"], tz=timezone.utc
            )
        elif "exp" in payload_dict and isinstance(payload_dict["exp"], float):
            payload_dict["exp"] = datetime.fromtimestamp(
                payload_dict["exp"], tz=timezone.utc
            )

        token_payload = TokenPayload(**payload_dict)

        # Check if token has expired
        if token_payload.exp and token_payload.exp < datetime.now(timezone.utc):
            # print("Token has expired") # Or raise an exception
            return None
        return token_payload
    except jwt.ExpiredSignatureError:
        # print("Token has expired (ExpiredSignatureError)")
        return None
    except jwt.PyJWTError as e:
        # print(f"Invalid token: {e}")
        return None
    except ValidationError as e:
        # print(f"Token payload validation error: {e}")
        return None


# Example usage (for testing this file directly):
# if __name__ == "__main__":
#     # Ensure settings are loaded if you run this standalone
#     # from app.core.config import settings # Already imported

#     user_id = "test_user_123"
#     print(f"JWT Secret: {settings.JWT_SECRET_KEY[:10]}...") # Don't print full secret
#     print(f"JWT Algo: {settings.JWT_ALGORITHM}")
#     print(f"Token Expire Mins: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")

#     token = create_access_token(subject=user_id)
#     print(f"Generated Token: {token}")

#     payload = decode_access_token(token)
#     if payload:
#         print(f"Decoded Payload: sub={payload.sub}, exp={payload.exp}")
#     else:
#         print("Failed to decode token or token invalid/expired.")

#     # Test expired token
#     expired_token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-1))
#     print(f"Generated Expired Token: {expired_token}")
#     payload_expired = decode_access_token(expired_token)
#     if payload_expired:
#         print(f"Decoded Expired Payload: {payload_expired}")
#     else:
#         print("Correctly identified expired token as invalid.")
