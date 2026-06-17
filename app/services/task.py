from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.task import task_repository
from app.repositories.user import user_repository
from app.schemas.task import TaskCreate, TaskSortBy, TaskUpdate


class TaskService:
    async def get_tasks(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date: datetime | None = None,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        sort_by: TaskSortBy = TaskSortBy.LATEST,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Retrieve tasks for an owner with optional filtering, sorting,

        and pagination.
        """
        return await task_repository.get_multi_by_owner(
            db,
            owner_id=owner_id,
            status=status,
            priority=priority,
            due_date=due_date,
            due_before=due_before,
            due_after=due_after,
            sort_by=sort_by.value,
            skip=skip,
            limit=limit,
        )

    async def get_assigned_tasks(
        self,
        db: AsyncSession,
        *,
        assignee_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        sort_by: TaskSortBy = TaskSortBy.LATEST,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Retrieve tasks assigned to a specific user with optional filtering,

        sorting, and pagination.
        """
        return await task_repository.get_assigned_to_user(
            db,
            assignee_id=assignee_id,
            status=status,
            priority=priority,
            sort_by=sort_by.value,
            skip=skip,
            limit=limit,
        )

    async def get_task(self, db: AsyncSession, *, id: int, user_id: int) -> Task:
        """Retrieve a task that the user owns or is assigned to.
        Raises NotFoundException if not found.
        """
        task = await task_repository.get_accessible_task(db, id=id, user_id=user_id)
        if not task:
            raise NotFoundException(
                message="Task not found or you do not have access to it."
            )
        return task

    async def create_task(
        self, db: AsyncSession, *, obj_in: TaskCreate, owner_id: int
    ) -> Task:
        """Create a new task, optionally assigning it to a user."""
        if obj_in.assignee_id is not None:
            assignee = await user_repository.get(db, id=obj_in.assignee_id)
            if not assignee:
                raise NotFoundException(message="Assignee user not found.")
        return await task_repository.create_with_owner(
            db, obj_in=obj_in, owner_id=owner_id
        )

    async def update_task(
        self, db: AsyncSession, *, id: int, user_id: int, obj_in: TaskUpdate
    ) -> Task:
        """Update a specific task. Both owner and assignee are authorized to update."""
        task = await self.get_task(db, id=id, user_id=user_id)
        if obj_in.assignee_id is not None:
            assignee = await user_repository.get(db, id=obj_in.assignee_id)
            if not assignee:
                raise NotFoundException(message="Assignee user not found.")
        return await task_repository.update(db, db_obj=task, obj_in=obj_in)

    async def delete_task(self, db: AsyncSession, *, id: int, user_id: int) -> Task:
        """Delete a specific task. Only the owner is authorized to delete."""
        task = await task_repository.get(db, id=id)
        if not task or (task.owner_id != user_id and task.assignee_id != user_id):
            raise NotFoundException(
                message="Task not found or you do not have access to it."
            )
        if task.owner_id != user_id:
            raise ForbiddenException(
                message="Only the task owner can delete this task."
            )
        await task_repository.remove(db, id=id)
        return task


task_service = TaskService()
