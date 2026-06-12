from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, ConflictException
from app.core.security import verify_password
from app.models.user import User
from app.repositories.user import user_repository
from app.schemas.user import UserCreate


class AuthService:
    async def register(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Register a new user, checking if the email is already taken."""
        user = await user_repository.get_by_email(db, email=obj_in.email)
        if user:
            raise ConflictException(
                message="A user with this email address already exists."
            )
        return await user_repository.create_user(db, obj_in=obj_in)

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> User:
        """Authenticate a user and return the user object if successful."""
        user = await user_repository.get_by_email(db, email=email)
        if not user:
            raise AuthenticationException(message="Incorrect email or password.")
        if not verify_password(password, user.hashed_password):
            raise AuthenticationException(message="Incorrect email or password.")
        if not user.is_active:
            raise AuthenticationException(message="User account is disabled.")
        return user


auth_service = AuthService()
