"""Alert system for backup failures and issues."""

import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

import requests

from src.database import DatabaseManager, Alert, Backup

logger = logging.getLogger(__name__)


class AlertSystem:
    """Sends alerts for backup failures and issues."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize alert system.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.alert_config = config.get("alerts", {})
        self.monitoring_config = config.get("monitoring", {})

    def send_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        location_id: Optional[int] = None,
        backup_id: Optional[int] = None,
    ) -> Alert:
        """Send alert and store in database.

        Args:
            alert_type: Type of alert.
            severity: Alert severity (critical, warning, info).
            message: Alert message.
            location_id: Optional location ID.
            backup_id: Optional backup ID.

        Returns:
            Alert object.
        """
        alert = self.db_manager.add_alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            location_id=location_id,
            backup_id=backup_id,
        )

        if self.alert_config.get("log", {}).get("enabled", True):
            log_level = self.alert_config.get("log", {}).get("level", "ERROR")
            if severity == "critical":
                logger.critical(
                    f"ALERT [{alert_type}]: {message}",
                    extra={
                        "alert_id": alert.id,
                        "alert_type": alert_type,
                        "severity": severity,
                        "location_id": location_id,
                        "backup_id": backup_id,
                    },
                )
            elif severity == "warning":
                logger.warning(
                    f"ALERT [{alert_type}]: {message}",
                    extra={
                        "alert_id": alert.id,
                        "alert_type": alert_type,
                        "severity": severity,
                    },
                )
            else:
                logger.info(
                    f"ALERT [{alert_type}]: {message}",
                    extra={
                        "alert_id": alert.id,
                        "alert_type": alert_type,
                        "severity": severity,
                    },
                )

        if self.alert_config.get("email", {}).get("enabled", False):
            self._send_email_alert(alert_type, severity, message)

        if self.alert_config.get("slack", {}).get("enabled", False):
            self._send_slack_alert(alert_type, severity, message)

        return alert

    def _send_email_alert(
        self, alert_type: str, severity: str, message: str
    ) -> None:
        """Send email alert.

        Args:
            alert_type: Type of alert.
            severity: Alert severity.
            message: Alert message.
        """
        email_config = self.alert_config.get("email", {})

        try:
            smtp_host = email_config.get("smtp_host", "smtp.gmail.com")
            smtp_port = email_config.get("smtp_port", 587)
            from_email = email_config.get("from_email", "")
            to_emails = email_config.get("to_emails", [])

            if not from_email or not to_emails:
                logger.warning(
                    "Email alert configured but from_email or to_emails not set",
                    extra={"from_email": from_email, "to_emails": to_emails},
                )
                return

            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"Backup Monitor Alert: {alert_type} - {severity.upper()}"

            body = f"""
Alert Type: {alert_type}
Severity: {severity}
Message: {message}
"""
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.send_message(msg)

            logger.info(
                f"Email alert sent for {alert_type}",
                extra={"alert_type": alert_type, "severity": severity},
            )

        except Exception as e:
            logger.error(
                f"Failed to send email alert: {e}",
                extra={"alert_type": alert_type, "error": str(e)},
            )

    def _send_slack_alert(
        self, alert_type: str, severity: str, message: str
    ) -> None:
        """Send Slack alert.

        Args:
            alert_type: Type of alert.
            severity: Alert severity.
            message: Alert message.
        """
        slack_config = self.alert_config.get("slack", {})
        webhook_url = slack_config.get("webhook_url", "")

        if not webhook_url:
            logger.warning("Slack alert configured but webhook_url not set")
            return

        try:
            color_map = {
                "critical": "#ff0000",
                "warning": "#ffaa00",
                "info": "#00aaff",
            }

            payload = {
                "attachments": [
                    {
                        "color": color_map.get(severity, "#808080"),
                        "title": f"Backup Monitor Alert: {alert_type}",
                        "fields": [
                            {"title": "Severity", "value": severity.upper(), "short": True},
                            {"title": "Message", "value": message, "short": False},
                        ],
                    }
                ]
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(
                f"Slack alert sent for {alert_type}",
                extra={"alert_type": alert_type, "severity": severity},
            )

        except Exception as e:
            logger.error(
                f"Failed to send Slack alert: {e}",
                extra={"alert_type": alert_type, "error": str(e)},
            )

    def check_and_alert_failures(
        self, location_id: Optional[int] = None, days: int = 1
    ) -> List[Alert]:
        """Check for backup failures and send alerts.

        Args:
            location_id: Optional location ID filter.
            days: Number of days to check.

        Returns:
            List of Alert objects created.
        """
        if not self.monitoring_config.get("alert_on_failure", True):
            return []

        failed_backups = self.db_manager.get_failed_backups(
            location_id=location_id, days=days
        )

        alerts = []

        for backup in failed_backups:
            existing_alerts = self.db_manager.get_unresolved_alerts(
                location_id=backup.location_id
            )

            alert_exists = any(
                a.backup_id == backup.id and a.alert_type == "backup_failure"
                for a in existing_alerts
            )

            if not alert_exists:
                alert = self.send_alert(
                    alert_type="backup_failure",
                    severity="critical",
                    message=f"Backup failed: {backup.filename} - {backup.error_message or 'Unknown error'}",
                    location_id=backup.location_id,
                    backup_id=backup.id,
                )
                alerts.append(alert)

        return alerts

    def check_and_alert_verification_failures(
        self, location_id: Optional[int] = None, days: int = 1
    ) -> List[Alert]:
        """Check for verification failures and send alerts.

        Args:
            location_id: Optional location ID filter.
            days: Number of days to check.

        Returns:
            List of Alert objects created.
        """
        if not self.monitoring_config.get("alert_on_verification_failure", True):
            return []

        from src.database import BackupVerification

        session = self.db_manager.get_session()
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = (
                session.query(BackupVerification)
                .filter(BackupVerification.status == "failed")
                .filter(BackupVerification.verified_at >= cutoff_date)
            )

            if location_id:
                query = query.join(Backup).filter(Backup.location_id == location_id)

            failed_verifications = query.all()

            alerts = []

            for verification in failed_verifications:
                existing_alerts = self.db_manager.get_unresolved_alerts(
                    backup_id=verification.backup_id
                )

                alert_exists = any(
                    a.alert_type == "verification_failure"
                    for a in existing_alerts
                )

                if not alert_exists:
                    alert = self.send_alert(
                        alert_type="verification_failure",
                        severity="warning",
                        message=f"Backup verification failed: {verification.verification_type} - {verification.error_message or verification.result}",
                        backup_id=verification.backup_id,
                    )
                    alerts.append(alert)

            return alerts
        finally:
            session.close()

    def check_and_alert_restore_failures(
        self, location_id: Optional[int] = None, days: int = 7
    ) -> List[Alert]:
        """Check for restore test failures and send alerts.

        Args:
            location_id: Optional location ID filter.
            days: Number of days to check.

        Returns:
            List of Alert objects created.
        """
        if not self.monitoring_config.get("alert_on_restore_failure", True):
            return []

        from src.database import RestoreTest

        session = self.db_manager.get_session()
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = (
                session.query(RestoreTest)
                .filter(RestoreTest.status == "failed")
                .filter(RestoreTest.tested_at >= cutoff_date)
            )

            if location_id:
                query = query.join(Backup).filter(Backup.location_id == location_id)

            failed_tests = query.all()

            alerts = []

            for test in failed_tests:
                existing_alerts = self.db_manager.get_unresolved_alerts(
                    backup_id=test.backup_id
                )

                alert_exists = any(
                    a.alert_type == "restore_failure"
                    for a in existing_alerts
                )

                if not alert_exists:
                    alert = self.send_alert(
                        alert_type="restore_failure",
                        severity="critical",
                        message=f"Restore test failed: {test.error_message or test.result}",
                        backup_id=test.backup_id,
                    )
                    alerts.append(alert)

            return alerts
        finally:
            session.close()
