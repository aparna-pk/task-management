from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate


class UserRepository(BaseRepository[User]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Fetch a user by their email address."""
        result = await db.execute(select(self.model).filter(self.model.email == email))
        return result.scalars().first()

    async def create_user(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create a user and automatically hash their password."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user_repository = UserRepository(User)
