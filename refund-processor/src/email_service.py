"""Email service for sending refund confirmations."""

import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending refund confirmation emails."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
        from_name: str,
        retry_attempts: int = 3,
        retry_delay_seconds: int = 5,
    ):
        """Initialize email service.

        Args:
            smtp_host: SMTP server hostname.
            smtp_port: SMTP server port.
            smtp_username: SMTP username.
            smtp_password: SMTP password.
            from_email: Sender email address.
            from_name: Sender display name.
            retry_attempts: Number of retry attempts.
            retry_delay_seconds: Delay between retries.
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds

        template_dir = Path(__file__).parent.parent / "templates"
        self.template_env = Environment(loader=FileSystemLoader(template_dir))

    def send_email(
        self, to_email: str, subject: str, body: str, is_html: bool = True
    ) -> bool:
        """Send email with retry logic.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
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
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)

                logger.info(f"Email sent successfully to {to_email}")
                return True

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Failed to send email (attempt {attempt}/{self.retry_attempts}): {e}"
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay_seconds)

        logger.error(
            f"Failed to send email after {self.retry_attempts} attempts: {last_exception}"
        )
        return False

    def send_refund_confirmation(
        self,
        to_email: str,
        customer_name: str,
        order_id: str,
        refund_amount: float,
        net_refund_amount: float,
        restocking_fee: float,
        currency: str,
        refund_reason: str,
        template_path: Optional[str] = None,
        subject_template: Optional[str] = None,
    ) -> bool:
        """Send refund confirmation email.

        Args:
            to_email: Recipient email address.
            customer_name: Customer name.
            order_id: Order identifier.
            refund_amount: Refund amount before fees.
            net_refund_amount: Net refund amount after fees.
            restocking_fee: Restocking fee amount.
            currency: Currency code.
            refund_reason: Reason for refund.
            template_path: Path to email template.
            subject_template: Email subject template.

        Returns:
            True if email sent successfully, False otherwise.
        """
        if template_path is None:
            template_path = "templates/refund_confirmation.html"

        if subject_template is None:
            subject_template = "Refund Confirmation - Order {{order_id}}"

        try:
            template = self.template_env.get_template(template_path)
        except TemplateNotFound:
            logger.warning(
                f"Template not found: {template_path}, using default template"
            )
            body = self._get_default_refund_body(
                customer_name,
                order_id,
                refund_amount,
                net_refund_amount,
                restocking_fee,
                currency,
                refund_reason,
            )
        else:
            body = template.render(
                customer_name=customer_name,
                order_id=order_id,
                refund_amount=refund_amount,
                net_refund_amount=net_refund_amount,
                restocking_fee=restocking_fee,
                currency=currency,
                refund_reason=refund_reason,
            )

        subject = subject_template.replace("{{order_id}}", order_id)

        return self.send_email(to_email, subject, body, is_html=True)

    @staticmethod
    def _get_default_refund_body(
        customer_name: str,
        order_id: str,
        refund_amount: float,
        net_refund_amount: float,
        restocking_fee: float,
        currency: str,
        refund_reason: str,
    ) -> str:
        """Generate default refund confirmation email body.

        Args:
            customer_name: Customer name.
            order_id: Order identifier.
            refund_amount: Refund amount.
            net_refund_amount: Net refund amount.
            restocking_fee: Restocking fee.
            currency: Currency code.
            refund_reason: Refund reason.

        Returns:
            HTML email body content.
        """
        currency_symbol = "$" if currency == "USD" else currency
        return f"""
        <html>
            <body>
                <h2>Refund Confirmation</h2>
                <p>Dear {customer_name},</p>
                <p>Your refund request for Order <strong>{order_id}</strong> has been processed.</p>
                <p><strong>Refund Details:</strong></p>
                <ul>
                    <li>Order ID: {order_id}</li>
                    <li>Refund Amount: {currency_symbol}{refund_amount:.2f}</li>
                    <li>Restocking Fee: {currency_symbol}{restocking_fee:.2f}</li>
                    <li>Net Refund Amount: {currency_symbol}{net_refund_amount:.2f}</li>
                    <li>Reason: {refund_reason}</li>
                </ul>
                <p>The refund will be processed to your original payment method within 5-10 business days.</p>
                <p>If you have any questions, please contact our support team.</p>
                <p>Thank you,<br>Refund Processing Team</p>
            </body>
        </html>
        """
