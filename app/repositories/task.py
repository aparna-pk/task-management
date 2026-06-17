from datetime import datetime

from sqlalchemy import case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskSortBy


class TaskRepository(BaseRepository[Task]):
    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date: datetime | None = None,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        sort_by: TaskSortBy | str = TaskSortBy.LATEST,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Fetch tasks belonging to a specific owner with filtering and sorting."""
        query = select(self.model).filter(self.model.owner_id == owner_id)

        # Filters
        if status is not None:
            query = query.filter(self.model.status == status)
        if priority is not None:
            query = query.filter(self.model.priority == priority)
        if due_date is not None:
            query = query.filter(self.model.due_date == due_date)
        if due_before is not None:
            query = query.filter(self.model.due_date <= due_before)
        if due_after is not None:
            query = query.filter(self.model.due_date >= due_after)

        # Sorting
        sort_key = sort_by.value if isinstance(sort_by, TaskSortBy) else sort_by
        if sort_key == TaskSortBy.PRIORITY.value:
            priority_order = case(
                (self.model.priority == TaskPriority.HIGH, 1),
                (self.model.priority == TaskPriority.MEDIUM, 2),
                (self.model.priority == TaskPriority.LOW, 3),
                else_=4,
            )
            query = query.order_by(priority_order.asc(), self.model.created_at.desc())
        elif sort_key == TaskSortBy.OLDEST.value:
            query = query.order_by(self.model.created_at.asc())
        else:
            query = query.order_by(self.model.created_at.desc())

        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_by_owner_and_id(
        self, db: AsyncSession, *, id: int, owner_id: int
    ) -> Task | None:
        """Fetch a single task belonging to a specific owner by ID."""
        result = await db.execute(
            select(self.model).filter(
                self.model.id == id, self.model.owner_id == owner_id
            )
        )
        return result.scalars().first()

    async def get_accessible_task(
        self, db: AsyncSession, *, id: int, user_id: int
    ) -> Task | None:
        """Fetch a task that the user owns or is assigned to."""
        result = await db.execute(
            select(self.model).filter(
                self.model.id == id,
                or_(
                    self.model.owner_id == user_id,
                    self.model.assignee_id == user_id,
                ),
            )
        )
        return result.scalars().first()

    async def get_assigned_to_user(
        self,
        db: AsyncSession,
        *,
        assignee_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        sort_by: TaskSortBy | str = TaskSortBy.LATEST,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Fetch tasks assigned to a specific user."""
        query = select(self.model).filter(self.model.assignee_id == assignee_id)

        if status is not None:
            query = query.filter(self.model.status == status)
        if priority is not None:
            query = query.filter(self.model.priority == priority)

        sort_key = sort_by.value if isinstance(sort_by, TaskSortBy) else sort_by
        if sort_key == TaskSortBy.PRIORITY.value:
            priority_order = case(
                (self.model.priority == TaskPriority.HIGH, 1),
                (self.model.priority == TaskPriority.MEDIUM, 2),
                (self.model.priority == TaskPriority.LOW, 3),
                else_=4,
            )
            query = query.order_by(priority_order.asc(), self.model.created_at.desc())
        elif sort_key == TaskSortBy.OLDEST.value:
            query = query.order_by(self.model.created_at.asc())
        else:
            query = query.order_by(self.model.created_at.desc())

        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

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
