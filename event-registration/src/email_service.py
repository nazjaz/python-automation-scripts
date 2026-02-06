"""Email service for sending confirmation and waitlist emails."""

import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Optional

from jinja2 import Template

from src.database import DatabaseManager, Registration, Event

logger = logging.getLogger(__name__)


class EmailService:
    """Sends confirmation and waitlist notification emails."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize email service.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.email_config = config.get("email", {})
        self.registration_config = config.get("registration", {})

        self.smtp_host = self.email_config.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = self.email_config.get("smtp_port", 587)
        self.from_email = self.email_config.get("from_email", "")
        self.from_name = self.email_config.get("from_name", "Event Registration")
        self.retry_attempts = self.email_config.get("retry_attempts", 3)
        self.retry_delay_seconds = self.email_config.get("retry_delay_seconds", 5)

    def send_confirmation_email(
        self, registration_id: int
    ) -> bool:
        """Send confirmation email to registrant.

        Args:
            registration_id: Registration ID.

        Returns:
            True if email sent successfully, False otherwise.
        """
        registration = (
            self.db_manager.get_session()
            .query(Registration)
            .filter(Registration.id == registration_id)
            .first()
        )

        if not registration:
            logger.error(
                f"Registration {registration_id} not found",
                extra={"registration_id": registration_id},
            )
            return False

        if registration.confirmation_sent:
            logger.debug(
                f"Confirmation already sent for registration {registration_id}",
                extra={"registration_id": registration_id},
            )
            return True

        event = self.db_manager.get_event(registration.event_id)

        if not event:
            logger.error(
                f"Event {registration.event_id} not found",
                extra={"event_id": registration.event_id},
            )
            return False

        confirmation_config = self.registration_config.get("confirmation_email", {})
        if not confirmation_config.get("enabled", True):
            logger.debug("Confirmation emails are disabled")
            return False

        template_path = Path(
            confirmation_config.get("template", "templates/confirmation_email.html")
        )

        if not template_path.is_absolute():
            template_path = Path(__file__).parent.parent / template_path

        subject_template = confirmation_config.get(
            "subject", "Event Registration Confirmation - {{event_name}}"
        )

        try:
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_confirmation_template()

            template = Template(template_content)
            subject_template_obj = Template(subject_template)

            email_data = {
                "event_name": event.name,
                "event_date": event.event_date.strftime("%Y-%m-%d %H:%M") if event.event_date else "",
                "event_location": event.location or "",
                "registrant_name": registration.name,
                "registrant_email": registration.email,
                "company": registration.company or "",
                "ticket_type": registration.ticket_type or "",
                "registration_id": registration.id,
            }

            html_body = template.render(**email_data)
            subject = subject_template_obj.render(**email_data)

            success = self._send_email(
                to_email=registration.email,
                subject=subject,
                html_body=html_body,
            )

            if success:
                registration.confirmation_sent = True
                session = self.db_manager.get_session()
                try:
                    session.merge(registration)
                    session.commit()
                finally:
                    session.close()

                logger.info(
                    f"Confirmation email sent to {registration.email}",
                    extra={
                        "registration_id": registration_id,
                        "email": registration.email,
                    },
                )

            return success

        except Exception as e:
            logger.error(
                f"Error sending confirmation email: {e}",
                extra={"registration_id": registration_id, "error": str(e)},
            )
            return False

    def send_waitlist_email(
        self, registration_id: int
    ) -> bool:
        """Send waitlist notification email to registrant.

        Args:
            registration_id: Registration ID.

        Returns:
            True if email sent successfully, False otherwise.
        """
        registration = (
            self.db_manager.get_session()
            .query(Registration)
            .filter(Registration.id == registration_id)
            .first()
        )

        if not registration or not registration.is_waitlist:
            return False

        event = self.db_manager.get_event(registration.event_id)

        if not event:
            return False

        waitlist_config = self.registration_config.get("waitlist_email", {})
        if not waitlist_config.get("enabled", True):
            return False

        template_path = Path(
            waitlist_config.get("template", "templates/waitlist_email.html")
        )

        if not template_path.is_absolute():
            template_path = Path(__file__).parent.parent / template_path

        subject_template = waitlist_config.get(
            "subject", "Waitlist Notification - {{event_name}}"
        )

        try:
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_waitlist_template()

            template = Template(template_content)
            subject_template_obj = Template(subject_template)

            email_data = {
                "event_name": event.name,
                "event_date": event.event_date.strftime("%Y-%m-%d %H:%M") if event.event_date else "",
                "registrant_name": registration.name,
                "waitlist_position": registration.waitlist_position or 0,
            }

            html_body = template.render(**email_data)
            subject = subject_template_obj.render(**email_data)

            return self._send_email(
                to_email=registration.email,
                subject=subject,
                html_body=html_body,
            )

        except Exception as e:
            logger.error(
                f"Error sending waitlist email: {e}",
                extra={"registration_id": registration_id, "error": str(e)},
            )
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """Send email with retry logic.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            html_body: HTML email body.

        Returns:
            True if email sent successfully, False otherwise.
        """
        import os

        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        if not smtp_username or not smtp_password:
            logger.warning(
                "SMTP credentials not configured, skipping email send",
                extra={"to_email": to_email},
            )
            return False

        for attempt in range(1, self.retry_attempts + 1):
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = f"{self.from_name} <{self.from_email}>"
                msg["To"] = to_email
                msg["Subject"] = subject

                msg.attach(MIMEText(html_body, "html"))

                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)

                return True

            except Exception as e:
                if attempt < self.retry_attempts:
                    logger.warning(
                        f"Email send attempt {attempt} failed, retrying: {e}",
                        extra={"attempt": attempt, "error": str(e)},
                    )
                    time.sleep(self.retry_delay_seconds)
                else:
                    logger.error(
                        f"Failed to send email after {self.retry_attempts} attempts: {e}",
                        extra={"to_email": to_email, "error": str(e)},
                    )

        return False

    def _get_default_confirmation_template(self) -> str:
        """Get default confirmation email template.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #667eea; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Registration Confirmed!</h1>
        </div>
        <div class="content">
            <p>Dear {{ registrant_name }},</p>
            <p>Your registration for <strong>{{ event_name }}</strong> has been confirmed.</p>
            <p><strong>Event Details:</strong></p>
            <ul>
                <li>Date: {{ event_date }}</li>
                <li>Location: {{ event_location }}</li>
            </ul>
            <p>We look forward to seeing you at the event!</p>
        </div>
        <div class="footer">
            <p>This is an automated confirmation email.</p>
        </div>
    </div>
</body>
</html>"""

    def _get_default_waitlist_template(self) -> str:
        """Get default waitlist email template.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ffc107; color: #333; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Waitlist Notification</h1>
        </div>
        <div class="content">
            <p>Dear {{ registrant_name }},</p>
            <p>Thank you for your interest in <strong>{{ event_name }}</strong>.</p>
            <p>The event is currently full, but we have added you to our waitlist.</p>
            <p>Your waitlist position: <strong>#{{ waitlist_position }}</strong></p>
            <p>We will notify you if a spot becomes available.</p>
        </div>
        <div class="footer">
            <p>This is an automated notification email.</p>
        </div>
    </div>
</body>
</html>"""
