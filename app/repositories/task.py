from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate


class TaskRepository(BaseRepository[Task]):
    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Fetch tasks belonging to a specific owner with pagination."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_owner_and_id(
        self, db: AsyncSession, *, id: int, owner_id: int
    ) -> Optional[Task]:
        """Fetch a single task belonging to a specific owner by ID."""
        result = await db.execute(
            select(self.model).filter(self.model.id == id, self.model.owner_id == owner_id)
        )
        return result.scalars().first()

    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: TaskCreate, owner_id: int
    ) -> Task:
        """Create a task associated with an owner ID."""
        db_obj = Task(**obj_in.model_dump(), owner_id=owner_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


task_repository = TaskRepository(Task)
