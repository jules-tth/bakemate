from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlmodel import Session, select

from app.models.calendar import CalendarEvent, CalendarEventCreate, CalendarEventUpdate, CalendarEventType
from app.models.user import User
from app.models.order import Order # For auto-populating order due dates
from app.repositories.sqlite_adapter import SQLiteRepository
# from app.services.google_calendar_service import GoogleCalendarService # Placeholder for future integration

class CalendarService:
    def __init__(self, session: Session):
        self.calendar_event_repo = SQLiteRepository(model=CalendarEvent) # type: ignore
        self.session = session
        # self.google_calendar_service = GoogleCalendarService() # Placeholder

    async def create_calendar_event(self, *, event_in: CalendarEventCreate, current_user: User) -> CalendarEvent:
        if event_in.user_id != current_user.id:
            # Handle error or override user_id
            pass
        
        db_event = await self.calendar_event_repo.create(obj_in=event_in)
        
        # Placeholder: If Google Calendar sync is enabled, create event in Google Calendar
        # if current_user.google_sync_enabled and db_event.event_type != CalendarEventType.ORDER_DUE_DATE: # Avoid double-syncing order dates if handled separately
        #     google_event_id = await self.google_calendar_service.create_event(db_event)
        #     if google_event_id:
        #         db_event.google_event_id = google_event_id
        #         db_event.google_calendar_id = current_user.primary_google_calendar_id # Assuming user has a primary calendar setting
        #         await self.calendar_event_repo.update(db_obj=db_event, obj_in={"google_event_id": google_event_id, "google_calendar_id": db_event.google_calendar_id})
        return db_event

    async def get_calendar_event_by_id(self, *, event_id: UUID, current_user: User) -> Optional[CalendarEvent]:
        event = await self.calendar_event_repo.get(id=event_id)
        if event and event.user_id == current_user.id:
            return event
        return None

    async def get_calendar_events_by_user(
        self, *, current_user: User, start_date: datetime, end_date: datetime, 
        event_type: Optional[CalendarEventType] = None, skip: int = 0, limit: int = 1000 # Higher limit for calendar views
    ) -> List[CalendarEvent]:
        filters: Dict[str, Any] = {
            "user_id": current_user.id,
            "start_datetime__lte": end_date, # Events that start before or at the end_date
            "end_datetime__gte": start_date,   # Events that end after or at the start_date
        }
        if event_type:
            filters["event_type"] = event_type
        
        events = await self.calendar_event_repo.get_multi(
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by="start_datetime" # Sort by start time
        )
        return events

    async def update_calendar_event(
        self, *, event_id: UUID, event_in: CalendarEventUpdate, current_user: User
    ) -> Optional[CalendarEvent]:
        db_event = await self.calendar_event_repo.get(id=event_id)
        if not db_event or db_event.user_id != current_user.id:
            return None
        
        updated_event = await self.calendar_event_repo.update(db_obj=db_event, obj_in=event_in)

        # Placeholder: If Google Calendar sync is enabled, update event in Google Calendar
        # if current_user.google_sync_enabled and updated_event.google_event_id:
        #     await self.google_calendar_service.update_event(updated_event)
        return updated_event

    async def delete_calendar_event(self, *, event_id: UUID, current_user: User) -> Optional[CalendarEvent]:
        db_event = await self.calendar_event_repo.get(id=event_id)
        if not db_event or db_event.user_id != current_user.id:
            return None
        
        # Placeholder: If Google Calendar sync is enabled, delete event from Google Calendar
        # if current_user.google_sync_enabled and db_event.google_event_id:
        #     await self.google_calendar_service.delete_event(db_event.google_event_id, db_event.google_calendar_id)

        deleted_event = await self.calendar_event_repo.delete(id=event_id)
        return deleted_event

    async def auto_populate_order_due_dates(self, *, order: Order, current_user: User):
        """    Creates or updates a calendar event for an order_s due date.
        This might be called when an order is created or its due date changes.
        """
        if not order.due_date:
            return

        # Check if an event already exists for this order_id
        existing_event_statement = select(CalendarEvent).where(CalendarEvent.order_id == order.id, CalendarEvent.user_id == current_user.id)
        existing_event = self.session.exec(existing_event_statement).first()

        event_data = CalendarEventUpdate(
            title=f"Order Due: {order.order_number}",
            start_datetime=order.due_date, # Assuming due_date is a specific time
            end_datetime=order.due_date + timedelta(hours=1), # Default 1 hour duration, or make it all-day
            is_all_day=False, # Or True if preferred for due dates
            event_type=CalendarEventType.ORDER_DUE_DATE,
            order_id=order.id,
            user_id=current_user.id # Needed for create if not existing
        )

        if existing_event:
            # Update existing event
            await self.update_calendar_event(event_id=existing_event.id, event_in=event_data, current_user=current_user)
        else:
            # Create new event
            create_data = CalendarEventCreate(**event_data.model_dump(exclude_unset=True), user_id=current_user.id)
            await self.create_calendar_event(event_in=create_data, current_user=current_user)
        
        # Placeholder: Google Calendar Sync for order due dates
        # This logic might be more complex if it needs to sync with a specific calendar for orders.
        print(f"Calendar event for order {order.order_number} due date auto-populated/updated.")

    # Placeholder for Google Calendar Sync methods
    async def sync_with_google_calendar(self, current_user: User):
        # 1. Fetch events from Google Calendar for the user_s linked calendar
        # 2. Fetch BakeMate calendar events for the user
        # 3. Diff and sync (create, update, delete in both directions or one-way)
        print(f"Placeholder: Syncing with Google Calendar for user {current_user.email}")
        pass

