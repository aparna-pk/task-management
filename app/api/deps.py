from typing import AsyncGenerator
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationException
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user import user_repository
from app.schemas.token import TokenPayload

# OAuth2 scheme config (defines where the token endpoint is located)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/oauth"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Dependency to retrieve and validate the current authenticated user from JWT token."""
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationException(message="Could not validate credentials.")

    try:
        token_data = TokenPayload(**payload)
    except Exception:
        raise AuthenticationException(message="Invalid token payload.")

    if token_data.sub is None:
        raise AuthenticationException(message="Could not validate credentials.")

    user = await user_repository.get(db, id=int(token_data.sub))
    if not user:
        raise AuthenticationException(message="User not found.")

    if not user.is_active:
        raise AuthenticationException(message="User account is inactive.")

    return user
