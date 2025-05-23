from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import date

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session
from app.services.mileage_service import MileageService
from app.models.mileage import MileageLog, MileageLogCreate, MileageLogRead, MileageLogUpdate
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=MileageLogRead, status_code=status.HTTP_201_CREATED)
async def create_mileage_log(
    *, 
    session: Session = Depends(get_session),
    log_in: MileageLogCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new mileage log for the authenticated user.
    """
    if log_in.user_id != current_user.id:
        # This should be handled by service or pre-validation
        pass
    mileage_service = MileageService(session=session)
    new_log = await mileage_service.create_mileage_log(log_in=log_in, current_user=current_user)
    return new_log

@router.get("/", response_model=List[MileageLogRead])
async def read_mileage_logs(
    *, 
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    purpose: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve mileage logs for the authenticated user, with optional filters.
    """
    mileage_service = MileageService(session=session)
    logs = await mileage_service.get_mileage_logs_by_user(
        current_user=current_user, start_date=start_date, end_date=end_date, purpose=purpose, skip=skip, limit=limit
    )
    return logs

@router.get("/{log_id}", response_model=MileageLogRead)
async def read_mileage_log(
    *, 
    session: Session = Depends(get_session),
    log_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific mileage log by ID for the authenticated user.
    """
    mileage_service = MileageService(session=session)
    log = await mileage_service.get_mileage_log_by_id(log_id=log_id, current_user=current_user)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mileage log not found or not owned by user")
    return log

@router.put("/{log_id}", response_model=MileageLogRead)
async def update_mileage_log(
    *, 
    session: Session = Depends(get_session),
    log_id: UUID,
    log_in: MileageLogUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a mileage log for the authenticated user.
    """
    mileage_service = MileageService(session=session)
    updated_log = await mileage_service.update_mileage_log(
        log_id=log_id, log_in=log_in, current_user=current_user
    )
    if not updated_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mileage log not found or not owned by user")
    return updated_log

@router.delete("/{log_id}", response_model=MileageLogRead)
async def delete_mileage_log(
    *, 
    session: Session = Depends(get_session),
    log_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a mileage log for the authenticated user.
    """
    mileage_service = MileageService(session=session)
    deleted_log = await mileage_service.delete_mileage_log(log_id=log_id, current_user=current_user)
    if not deleted_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mileage log not found or not owned by user")
    return deleted_log

