from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session
from app.services.calendar_service import CalendarService
from app.models.calendar import CalendarEvent, CalendarEventCreate, CalendarEventRead, CalendarEventUpdate, CalendarEventType
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()

@router.post("/events/", response_model=CalendarEventRead, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    *, 
    session: Session = Depends(get_session),
    event_in: CalendarEventCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new calendar event for the authenticated user.
    """
    if event_in.user_id != current_user.id:
        # This should be handled by service or pre-validation
        pass
    calendar_service = CalendarService(session=session)
    new_event = await calendar_service.create_calendar_event(event_in=event_in, current_user=current_user)
    return new_event

@router.get("/events/", response_model=List[CalendarEventRead])
async def read_calendar_events(
    *, 
    session: Session = Depends(get_session),
    start_date: datetime = Query(..., description="Start date/time for filtering events (ISO format)"),
    end_date: datetime = Query(..., description="End date/time for filtering events (ISO format)"),
    event_type: Optional[CalendarEventType] = Query(None, description="Filter by event type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=2000), # Default high limit for calendar views
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve calendar events for the authenticated user within a date range.
    """
    calendar_service = CalendarService(session=session)
    events = await calendar_service.get_calendar_events_by_user(
        current_user=current_user, start_date=start_date, end_date=end_date, 
        event_type=event_type, skip=skip, limit=limit
    )
    return events

@router.get("/events/{event_id}", response_model=CalendarEventRead)
async def read_calendar_event(
    *, 
    session: Session = Depends(get_session),
    event_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific calendar event by ID for the authenticated user.
    """
    calendar_service = CalendarService(session=session)
    event = await calendar_service.get_calendar_event_by_id(event_id=event_id, current_user=current_user)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found or not owned by user")
    return event

@router.put("/events/{event_id}", response_model=CalendarEventRead)
async def update_calendar_event(
    *, 
    session: Session = Depends(get_session),
    event_id: UUID,
    event_in: CalendarEventUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a calendar event for the authenticated user.
    """
    calendar_service = CalendarService(session=session)
    updated_event = await calendar_service.update_calendar_event(
        event_id=event_id, event_in=event_in, current_user=current_user
    )
    if not updated_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found or not owned by user")
    return updated_event

@router.delete("/events/{event_id}", response_model=CalendarEventRead) # Or status 204
async def delete_calendar_event(
    *, 
    session: Session = Depends(get_session),
    event_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a calendar event for the authenticated user.
    """
    calendar_service = CalendarService(session=session)
    deleted_event = await calendar_service.delete_calendar_event(event_id=event_id, current_user=current_user)
    if not deleted_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found or not owned by user")
    return deleted_event

# Placeholder for Google Calendar Sync endpoint
# @router.post("/sync/google", status_code=status.HTTP_202_ACCEPTED)
# async def trigger_google_calendar_sync(
#     *, 
#     session: Session = Depends(get_session),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """Trigger a two-way sync with Google Calendar."""
#     if not current_user.google_sync_enabled or not current_user.google_refresh_token:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Calendar sync is not enabled or configured for this user.")
#     calendar_service = CalendarService(session=session)
#     await calendar_service.sync_with_google_calendar(current_user=current_user)
#     return {"message": "Google Calendar synchronization process initiated."}

