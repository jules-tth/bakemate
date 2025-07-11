from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select
from sqlalchemy import func

from app.models.user import User
from app.models.contact import (
    Contact,
)  # Assuming Contact model exists and stores customer info
from app.models.order import (
    Order,
    OrderStatus,
)  # To identify top customers or dormant ones
from app.services.email_service import (
    EmailService,
)  # For sending campaigns via SendGrid
from app.core.config import settings


class MarketingSegment:
    TOP_CUSTOMERS = "top_customers"
    DORMANT_CUSTOMERS = "dormant_customers"
    # ALL_CONTACTS = "all_contacts" # Could be another segment


class MarketingService:
    def __init__(self, session: Session):
        self.session = session
        self.email_service = EmailService()

    async def get_contacts_for_segment(
        self, segment_type: str, current_user: User
    ) -> List[Contact]:
        """Retrieves contacts belonging to a specific dynamic segment."""
        contacts: List[Contact] = []

        if segment_type == MarketingSegment.TOP_CUSTOMERS:
            # Define "Top Customers": e.g., top 10% by total order value in the last year, or > X orders
            # This is a simplified version: customers with more than 2 completed orders.
            orders_subquery = (
                select(Order.customer_email, func.count(Order.id).label("order_count"))
                .where(
                    Order.user_id == current_user.id,
                    Order.status == OrderStatus.COMPLETED,
                )
                .group_by(Order.customer_email)
                .having(func.count(Order.id) > 2)
            )  # Example: more than 2 orders

            top_customer_emails_result = self.session.exec(orders_subquery).all()
            top_customer_emails = [
                row.customer_email
                for row in top_customer_emails_result
                if row.customer_email
            ]

            if top_customer_emails:
                contacts_stmt = select(Contact).where(
                    Contact.user_id == current_user.id,
                    Contact.email.in_(top_customer_emails),
                )
                contacts = self.session.exec(contacts_stmt).all()

        elif segment_type == MarketingSegment.DORMANT_CUSTOMERS:
            # Define "Dormant Customers": e.g., made an order but not in the last 6 months.
            six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)

            # Find emails of customers who have ordered at any time
            all_ordering_customers_stmt = select(Order.customer_email.distinct()).where(
                Order.user_id == current_user.id
            )
            all_ordering_emails = [
                email
                for email in self.session.exec(all_ordering_customers_stmt).all()
                if email
            ]

            # Find emails of customers who have ordered in the last 6 months
            recent_ordering_customers_stmt = select(
                Order.customer_email.distinct()
            ).where(
                Order.user_id == current_user.id, Order.order_date >= six_months_ago
            )
            recent_ordering_emails = [
                email
                for email in self.session.exec(recent_ordering_customers_stmt).all()
                if email
            ]

            dormant_emails = list(
                set(all_ordering_emails) - set(recent_ordering_emails)
            )

            if dormant_emails:
                contacts_stmt = select(Contact).where(
                    Contact.user_id == current_user.id,
                    Contact.email.in_(dormant_emails),
                )
                contacts = self.session.exec(contacts_stmt).all()

        # elif segment_type == MarketingSegment.ALL_CONTACTS:
        #     contacts_stmt = select(Contact).where(Contact.user_id == current_user.id)
        #     contacts = self.session.exec(contacts_stmt).all()

        return contacts

    async def send_campaign_to_segment(
        self,
        *,
        segment_type: str,
        subject: str,
        html_content: str,  # Basic templated HTML content
        current_user: User,
    ) -> Dict[str, Any]:
        """Sends a campaign email to all contacts in a specified segment."""
        if not settings.SENDGRID_API_KEY or not settings.EMAILS_FROM_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service (SendGrid) is not configured.",
            )

        contacts_to_email = await self.get_contacts_for_segment(
            segment_type=segment_type, current_user=current_user
        )

        if not contacts_to_email:
            return {
                "message": "No contacts found for the selected segment.",
                "sent_count": 0,
                "failed_count": 0,
            }

        sent_count = 0
        failed_contacts: List[str] = []

        # For SendGrid, it_s better to use batch sending or personalization if sending to many.
        # For simplicity here, sending one by one (not recommended for large lists).
        for contact in contacts_to_email:
            if not contact.email:
                failed_contacts.append(f"Contact ID {contact.id} missing email")
                continue
            try:
                # Here, html_content is the pre-crafted email body.
                # A more advanced system would use SendGrid templates and dynamic data.
                await self.email_service.send_email(
                    to_email=contact.email,
                    subject_template=subject,  # Using subject directly as template
                    html_template=html_content,  # Using html_content directly as template
                    environment={},
                )
                sent_count += 1
            except Exception as e:
                print(f"Failed to send campaign email to {contact.email}: {e}")
                failed_contacts.append(contact.email)

        return {
            "message": f"Campaign processed for segment {segment_type}.",
            "total_contacts_in_segment": len(contacts_to_email),
            "sent_count": sent_count,
            "failed_count": len(failed_contacts),
            "failed_recipients": failed_contacts,  # Be mindful of exposing PII in logs/responses
        }

    # Placeholder for UI to craft/basic-templated SendGrid campaign
    # The actual crafting UI would be in the frontend.
    # This service would take the crafted subject and HTML content.
    # A simple template example:
    def get_basic_campaign_template(
        self,
        title: str,
        body_paragraph: str,
        cta_text: str,
        cta_url: str,
        shop_name: str,
    ) -> str:
        """Generates a very basic HTML email template string."""
        # This is extremely basic. Real templates would be more robust.
        html_template = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 20px; padding: 0; background-color: #f9f7f5;">
                <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h1 style="color: #333;">{shop_name}</h1>
                    <h2 style="color: #555;">{title}</h2>
                    <p style="color: #666; line-height: 1.6;">{body_paragraph}</p>
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="{cta_url}" style="background-color: #FFB6C1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                            {cta_text}
                        </a>
                    </p>
                    <p style="margin-top: 30px; font-size: 0.9em; color: #888; text-align: center;">
                        If you have any questions, feel free to contact us.
                    </p>
                    <p style="font-size: 0.8em; color: #aaa; text-align: center; margin-top: 20px;">
                        You are receiving this email because you are a valued customer of {shop_name}.
                        <br>
                        {shop_name} - Bake with Love
                    </p>
                </div>
            </body>
        </html>
        """
        return html_template
