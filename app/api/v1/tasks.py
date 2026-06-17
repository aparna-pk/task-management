from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskSortBy, TaskUpdate
from app.services.task import task_service

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def read_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: TaskStatus | None = Query(None, description="Filter by task status"),
    priority: TaskPriority | None = Query(None, description="Filter by task priority"),
    due_date: datetime | None = Query(
        None, description="Filter tasks with an exact due date"
    ),
    due_before: datetime | None = Query(
        None, description="Filter tasks due on or before this datetime"
    ),
    due_after: datetime | None = Query(
        None, description="Filter tasks due on or after this datetime"
    ),
    sort_by: TaskSortBy = Query(
        TaskSortBy.LATEST, description="Sort order: latest, oldest, or priority"
    ),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[Task]:
    """Retrieve tasks with optional filtering, sorting, and pagination."""
    return await task_service.get_tasks(
        db,
        owner_id=current_user.id,
        status=status,
        priority=priority,
        due_date=due_date,
        due_before=due_before,
        due_after=due_after,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )


@router.get("/assigned", response_model=list[TaskResponse])
async def read_assigned_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: TaskStatus | None = Query(None, description="Filter by task status"),
    priority: TaskPriority | None = Query(None, description="Filter by task priority"),
    sort_by: TaskSortBy = Query(
        TaskSortBy.LATEST, description="Sort order: latest, oldest, or priority"
    ),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[Task]:
    """Retrieve tasks assigned to the current user."""
    return await task_service.get_assigned_tasks(
        db,
        assignee_id=current_user.id,
        status=status,
        priority=priority,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(
    task_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Task:
    """Retrieve details of a specific task."""
    return await task_service.get_task(db, id=task_id, user_id=current_user.id)


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Task:
    """Create a new task for the current user."""
    return await task_service.create_task(db, obj_in=task_in, owner_id=current_user.id)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Task:
    """Update a task's title, description, status, priority, due date, or assignee."""
    return await task_service.update_task(
        db, id=task_id, user_id=current_user.id, obj_in=task_in
    )


@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(
    task_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Task:
    """Delete a task from the database."""
    return await task_service.delete_task(db, id=task_id, user_id=current_user.id)
