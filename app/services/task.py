from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.models.task import Task
from app.repositories.task import task_repository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    async def get_tasks(
        self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Retrieve all tasks belonging to a specific owner with pagination."""
        return await task_repository.get_multi_by_owner(
            db, owner_id=owner_id, skip=skip, limit=limit
        )

    async def get_task(self, db: AsyncSession, *, id: int, owner_id: int) -> Task:
        """Retrieve a specific task belonging to an owner. Raises NotFoundException if not found."""
        task = await task_repository.get_by_owner_and_id(db, id=id, owner_id=owner_id)
        if not task:
            raise NotFoundException(message="Task not found or you do not have access to it.")
        return task

    async def create_task(self, db: AsyncSession, *, obj_in: TaskCreate, owner_id: int) -> Task:
        """Create a new task for an owner."""
        return await task_repository.create_with_owner(db, obj_in=obj_in, owner_id=owner_id)

    async def update_task(
        self, db: AsyncSession, *, id: int, owner_id: int, obj_in: TaskUpdate
    ) -> Task:
        """Update a specific task belonging to an owner."""
        task = await self.get_task(db, id=id, owner_id=owner_id)
        return await task_repository.update(db, db_obj=task, obj_in=obj_in)

    async def delete_task(self, db: AsyncSession, *, id: int, owner_id: int) -> Task:
        """Delete a specific task belonging to an owner."""
        task = await self.get_task(db, id=id, owner_id=owner_id)
        await task_repository.remove(db, id=id)
        return task


task_service = TaskService()
