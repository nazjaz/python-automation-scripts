"""Email service for sending welcome emails and notifications."""

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str,
        retry_attempts: int = 3,
        retry_delay_seconds: int = 5,
    ):
        """Initialize email service.

        Args:
            host: SMTP server hostname.
            port: SMTP server port.
            username: SMTP authentication username.
            password: SMTP authentication password.
            from_email: Sender email address.
            from_name: Sender display name.
            retry_attempts: Number of retry attempts for failed sends.
            retry_delay_seconds: Delay between retry attempts.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.template_env = Environment(
            loader=FileSystemLoader(Path(__file__).parent.parent)
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
    ) -> bool:
        """Send email with retry logic.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            body: Email body content.
            is_html: Whether body contains HTML.

        Returns:
            True if email sent successfully, False otherwise.
        """
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))

        last_exception = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
                logger.info(
                    f"Email sent successfully to {to_email}",
                    extra={"to": to_email, "subject": subject},
                )
                return True
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Failed to send email (attempt {attempt}/{self.retry_attempts}): {e}",
                    extra={"to": to_email, "attempt": attempt},
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay_seconds)

        logger.error(
            f"Failed to send email after {self.retry_attempts} attempts: {last_exception}",
            extra={"to": to_email, "error": str(last_exception)},
        )
        return False

    def send_welcome_email(
        self,
        to_email: str,
        customer_name: str,
        company_name: Optional[str] = None,
        template_path: Optional[str] = None,
        subject_template: Optional[str] = None,
    ) -> bool:
        """Send welcome email to new customer.

        Args:
            to_email: Recipient email address.
            customer_name: Customer's full name.
            company_name: Optional company name.
            template_path: Path to email template file.
            subject_template: Email subject template with placeholders.

        Returns:
            True if email sent successfully, False otherwise.
        """
        if template_path is None:
            template_path = "templates/welcome_email.html"

        if subject_template is None:
            subject_template = "Welcome to {{company_name}}"

        try:
            template = self.template_env.get_template(template_path)
        except TemplateNotFound:
            logger.warning(
                f"Template not found: {template_path}, using default template",
                extra={"template_path": template_path},
            )
            body = self._get_default_welcome_body(customer_name, company_name)
        else:
            body = template.render(
                customer_name=customer_name, company_name=company_name or "our platform"
            )

        subject = subject_template.replace("{{company_name}}", company_name or "our platform")

        return self.send_email(to_email, subject, body, is_html=True)

    @staticmethod
    def _get_default_welcome_body(customer_name: str, company_name: Optional[str]) -> str:
        """Generate default welcome email body if template not found.

        Args:
            customer_name: Customer's full name.
            company_name: Optional company name.

        Returns:
            HTML email body content.
        """
        company = company_name or "our platform"
        return f"""
        <html>
            <body>
                <h2>Welcome, {customer_name}!</h2>
                <p>Thank you for joining {company}. We're excited to have you on board.</p>
                <p>Your account setup is in progress, and you'll receive additional information shortly.</p>
                <p>If you have any questions, please don't hesitate to reach out to our support team.</p>
                <p>Best regards,<br>The {company} Team</p>
            </body>
        </html>
        """
