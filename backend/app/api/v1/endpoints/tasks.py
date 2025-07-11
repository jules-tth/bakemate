from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session
from app.services.task_service import TaskService
from app.models.task import Task, TaskCreate, TaskRead, TaskUpdate, TaskStatus
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    *,
    session: Session = Depends(get_session),
    task_in: TaskCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new task for the authenticated user.
    """
    if task_in.user_id != current_user.id:
        # This should be handled by service or pre-validation
        pass
    task_service = TaskService(session=session)
    new_task = await task_service.create_task(
        task_in=task_in, current_user=current_user
    )
    return new_task


@router.get("/", response_model=List[TaskRead])
async def read_tasks(
    *,
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority_filter: Optional[int] = Query(None, alias="priority"),
    due_date_start: Optional[datetime] = Query(
        None, description="Filter tasks due on or after this date (ISO format)"
    ),
    due_date_end: Optional[datetime] = Query(
        None, description="Filter tasks due on or before this date (ISO format)"
    ),
    order_id_filter: Optional[UUID] = Query(None, alias="order_id"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve tasks for the authenticated user, with optional filters.
    """
    task_service = TaskService(session=session)
    tasks = await task_service.get_tasks_by_user(
        current_user=current_user,
        status=status_filter,
        priority=priority_filter,
        due_date_start=due_date_start,
        due_date_end=due_date_end,
        order_id=order_id_filter,
        skip=skip,
        limit=limit,
    )
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
    *,
    session: Session = Depends(get_session),
    task_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific task by ID for the authenticated user.
    """
    task_service = TaskService(session=session)
    task = await task_service.get_task_by_id(task_id=task_id, current_user=current_user)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not owned by user",
        )
    return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    *,
    session: Session = Depends(get_session),
    task_id: UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a task for the authenticated user.
    """
    task_service = TaskService(session=session)
    updated_task = await task_service.update_task(
        task_id=task_id, task_in=task_in, current_user=current_user
    )
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not owned by user",
        )
    return updated_task


@router.delete("/{task_id}", response_model=TaskRead)  # Or status 204
async def delete_task(
    *,
    session: Session = Depends(get_session),
    task_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a task for the authenticated user.
    """
    task_service = TaskService(session=session)
    deleted_task = await task_service.delete_task(
        task_id=task_id, current_user=current_user
    )
    if not deleted_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not owned by user",
        )
    return deleted_task


# Placeholder for triggering weekly digest email (actual sending is via cron)
@router.post("/send-weekly-digest", status_code=status.HTTP_202_ACCEPTED)
async def trigger_weekly_digest(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually trigger the weekly digest email generation for the current user.
    (In production, this would be a cron job, this endpoint is for testing/dev)
    """
    task_service = TaskService(session=session)
    # Ensure SendGrid is configured if this is to actually send an email
    if not settings.SENDGRID_API_KEY or not settings.EMAILS_FROM_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured.",
        )

    await task_service.send_weekly_digest_email(current_user=current_user)
    return {"message": "Weekly digest email generation process initiated."}
