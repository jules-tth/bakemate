from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlmodel import Session, select

from app.models.task import Task, TaskCreate, TaskUpdate, TaskStatus
from app.models.user import User
from app.models.order import Order # For linking tasks to orders
from app.repositories.sqlite_adapter import SQLiteRepository
from app.services.email_service import EmailService # Updated to import the EmailService class
from app.core.config import settings

class TaskService:
    def __init__(self, session: Session):
        self.task_repo = SQLiteRepository(model=Task) # type: ignore
        self.session = session
        self.email_service = EmailService() # Instantiate EmailService

    async def create_task(self, *, task_in: TaskCreate, current_user: User) -> Task:
        if task_in.user_id != current_user.id:
            # Handle error or override user_id
            pass
        db_task = await self.task_repo.create(obj_in=task_in)
        return db_task

    async def get_task_by_id(self, *, task_id: UUID, current_user: User) -> Optional[Task]:
        task = await self.task_repo.get(id=task_id)
        if task and task.user_id == current_user.id:
            return task
        return None

    async def get_tasks_by_user(
        self, *, current_user: User, 
        status: Optional[TaskStatus] = None, 
        priority: Optional[int] = None,
        due_date_start: Optional[datetime] = None,
        due_date_end: Optional[datetime] = None,
        order_id: Optional[UUID] = None,
        skip: int = 0, limit: int = 100
    ) -> List[Task]:
        filters: Dict[str, Any] = {"user_id": current_user.id}
        if status:
            filters["status"] = status
        if priority is not None:
            filters["priority"] = priority
        if order_id:
            filters["order_id"] = order_id
        if due_date_start:
            filters["due_date__gte"] = due_date_start
        if due_date_end:
            filters["due_date__lte"] = due_date_end
            
        tasks = await self.task_repo.get_multi(
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by="due_date" # Sort by due date by default
        )
        return tasks

    async def update_task(
        self, *, task_id: UUID, task_in: TaskUpdate, current_user: User
    ) -> Optional[Task]:
        db_task = await self.task_repo.get(id=task_id)
        if not db_task or db_task.user_id != current_user.id:
            return None
        updated_task = await self.task_repo.update(db_obj=db_task, obj_in=task_in)
        return updated_task

    async def delete_task(self, *, task_id: UUID, current_user: User) -> Optional[Task]:
        db_task = await self.task_repo.get(id=task_id)
        if not db_task or db_task.user_id != current_user.id:
            return None
        deleted_task = await self.task_repo.delete(id=task_id)
        return deleted_task

    async def send_weekly_digest_email(self, current_user: User):
        """    Generates and sends a weekly digest email of upcoming orders and tasks.
        This would typically be triggered by a cron job on Monday 6 AM ET.
        """
        # Get upcoming week_s start and end (e.g., Monday to Sunday)
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        end_of_week = start_of_week + timedelta(days=6) # Sunday

        start_datetime = datetime.combine(start_of_week, datetime.min.time())
        end_datetime = datetime.combine(end_of_week, datetime.max.time())

        # Fetch upcoming tasks for the week
        upcoming_tasks = await self.get_tasks_by_user(
            current_user=current_user, 
            due_date_start=start_datetime, 
            due_date_end=end_datetime,
            status=TaskStatus.PENDING # Only pending or in_progress tasks
        )

        order_statement = select(Order).where(
            Order.user_id == current_user.id,
            Order.due_date >= start_datetime,
            Order.due_date <= end_datetime,
            Order.status.notin_([OrderStatus.COMPLETED, OrderStatus.CANCELLED]) # type: ignore
        ).order_by(Order.due_date)
        upcoming_orders = self.session.exec(order_statement).all()

        if not upcoming_tasks and not upcoming_orders:
            print(f"No upcoming tasks or orders for user {current_user.email} for the week. Digest not sent.")
            return

        email_subject = f"Your BakeMate Weekly Digest: {start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')}"
        
        html_content_parts = [f"<h1>Your BakeMate Weekly Digest</h1>"]
        html_content_parts.append(f"<p>Here_s what_s on your plate for {start_of_week.strftime('%B %d, %Y')} - {end_of_week.strftime('%B %d, %Y')}:<\/p>")

        if upcoming_orders:
            html_content_parts.append("<h2>Upcoming Orders:<\/h2><ul>")
            for order in upcoming_orders:
                html_content_parts.append(f"<li><strong>{order.order_number}<\/strong> - Due: {order.due_date.strftime('%a, %b %d, %I:%M %p')} - Status: {order.status.value}<\/li>")
            html_content_parts.append("<\/ul>")
        else:
            html_content_parts.append("<p>No upcoming orders this week.<\/p>")

        if upcoming_tasks:
            html_content_parts.append("<h2>Upcoming Tasks:<\/h2><ul>")
            for task in upcoming_tasks:
                due_str = task.due_date.strftime('%a, %b %d, %I:%M %p') if task.due_date else "N\/A"
                html_content_parts.append(f"<li><strong>{task.title}<\/strong> - Due: {due_str} - Priority: {task.priority} - Status: {task.status.value}<\/li>")
            html_content_parts.append("<\/ul>")
        else:
            html_content_parts.append("<p>No upcoming tasks this week.<\/p>")
        
        html_content = "".join(html_content_parts)

        # Use the email service instance to send the email
        await self.email_service.send_email_with_template_async(
            email_to=current_user.email,
            subject_template_str=email_subject, # Subject is already formatted
            html_template_name="weekly_digest_dynamic.html", # This template isn_t loaded, content is dynamic
            environment={"dynamic_html_content": html_content} # Pass dynamic content
        )
        print(f"Weekly digest email sent to {current_user.email}")
