"""Notification service for sending emails and SMS."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via email and SMS."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
        from_name: str,
    ):
        """Initialize notification service.

        Args:
            smtp_host: SMTP server hostname.
            smtp_port: SMTP server port.
            smtp_username: SMTP username.
            smtp_password: SMTP password.
            from_email: Sender email address.
            from_name: Sender display name.
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name

    def send_email(
        self, to_email: str, subject: str, body: str, is_html: bool = True
    ) -> bool:
        """Send email notification.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            body: Email body content.
            is_html: Whether body contains HTML.

        Returns:
            True if email sent successfully, False otherwise.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_travel_reminder(
        self,
        to_email: str,
        traveler_name: str,
        trip_start_date: str,
        destination: str,
        hours_until: int,
    ) -> bool:
        """Send travel reminder email.

        Args:
            to_email: Recipient email address.
            traveler_name: Traveler's name.
            trip_start_date: Trip start date as string.
            destination: Trip destination.
            hours_until: Hours until trip starts.

        Returns:
            True if email sent successfully, False otherwise.
        """
        subject = f"Travel Reminder: Your trip to {destination} starts in {hours_until} hours"
        body = f"""
        <html>
            <body>
                <h2>Travel Reminder</h2>
                <p>Hi {traveler_name},</p>
                <p>This is a reminder that your trip to <strong>{destination}</strong> starts in <strong>{hours_until} hours</strong>.</p>
                <p>Trip Start Date: {trip_start_date}</p>
                <p>Please ensure you have all necessary documents and confirmations ready.</p>
                <p>Safe travels!</p>
            </body>
        </html>
        """

        return self.send_email(to_email, subject, body, is_html=True)

    def send_update_notification(
        self,
        to_email: str,
        traveler_name: str,
        update_type: str,
        update_message: str,
    ) -> bool:
        """Send travel update notification.

        Args:
            to_email: Recipient email address.
            traveler_name: Traveler's name.
            update_type: Type of update (gate_change, delay, etc.).
            update_message: Update message.

        Returns:
            True if email sent successfully, False otherwise.
        """
        subject = f"Travel Update: {update_type.replace('_', ' ').title()}"
        body = f"""
        <html>
            <body>
                <h2>Travel Update</h2>
                <p>Hi {traveler_name},</p>
                <p>{update_message}</p>
                <p>Please check your itinerary for the latest information.</p>
            </body>
        </html>
        """

        return self.send_email(to_email, subject, body, is_html=True)
