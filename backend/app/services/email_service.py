import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, Content, MimeType

from app.core.config import settings


class EmailService:
    """
    EmailService provides email sending capabilities using SendGrid.

    Methods:
        send_email_async(email_to, subject, html_content, email_from=settings.EMAIL_FROM):
            Asynchronously sends an email with the specified subject and HTML content to the email_to address.

        send_email_with_template_async(email_to, subject_template_str, html_template_name, environment=None):
            Asynchronously sends a templated email, allowing for dynamic subject and HTML content based on provided environment variables.
    """

    async def send_email_async(
        self,
        email_to: str,
        subject: str,
        html_content: str,
        email_from: str = settings.EMAIL_FROM,
    ) -> bool:
        """
        Sends an email using SendGrid.

        Args:
            email_to: The recipient's email address.
            subject: The subject of the email.
            html_content: The HTML content of the email.
            email_from: The sender's email address (defaults to settings.EMAIL_FROM).

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        if (
            not settings.SENDGRID_API_KEY
            or settings.SENDGRID_API_KEY == "YOUR_SENDGRID_API_KEY_HERE"
        ):
            print(f"SENDGRID_API_KEY not configured. Skipping email to {email_to}.")
            print(f"Subject: {subject}")
            print(f"HTML Content (first 100 chars): {html_content[:100]}...")
            return True

        message = Mail(
            from_email=From(email_from, settings.PROJECT_NAME),
            to_emails=To(email_to),
            subject=Subject(subject),
            html_content=Content(MimeType.html, html_content),
        )
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            return 200 <= response.status_code < 300
        except Exception as e:
            print(f'Error sending email to {email_to} with subject "{subject}": {e}')
            return False

    async def send_email_with_template_async(
        self,
        email_to: str,
        subject_template_str: str,
        html_template_name: str,
        environment: dict = None,
    ) -> bool:
        """
        Sends an email using a pre-defined HTML template (template loading not implemented here).

        Args:
            email_to: The recipient's email address.
            subject_template_str: Template for the email subject.
            html_template_name: Name of the HTML template to use (placeholder implementation).
            environment: Dictionary of template variables.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        if environment is None:
            environment = {}

        subject = subject_template_str.format(**environment)
        html_content_parts = [f"<h1>{subject}</h1>"]
        for key, value in environment.items():
            html_content_parts.append(
                f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
            )
        html_content = "".join(html_content_parts)

        if "verification_link" in environment:
            html_content += f"<p>Please <a href='{environment['verification_link']}'>click here to verify</a>.</p>"
        elif "reset_password_link" in environment:
            html_content += f"<p>Please <a href='{environment['reset_password_link']}'>click here to reset your password</a>.</p>"

        return await self.send_email_async(
            email_to=email_to, subject=subject, html_content=html_content
        )
