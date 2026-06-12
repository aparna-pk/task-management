from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task import task_service

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def read_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[Task]:
    """Retrieve tasks belonging to the current user with pagination."""
    return await task_service.get_tasks(
        db, owner_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(
    task_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Task:
    """Retrieve details of a specific task."""
    return await task_service.get_task(db, id=task_id, owner_id=current_user.id)


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
    """Update a task's title, description, status, or due date."""
    return await task_service.update_task(
        db, id=task_id, owner_id=current_user.id, obj_in=task_in
    )


@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(
    task_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Task:
    """Delete a task from the database."""
    return await task_service.delete_task(db, id=task_id, owner_id=current_user.id)
