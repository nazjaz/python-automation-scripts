"""Send alerts for pipeline issues."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class Alerting:
    """Send alerts for pipeline issues."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize alerting system.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.alert_channels = config.get("alert_channels", {})
        self.alert_rules = config.get("alert_rules", {})

    def send_alert(
        self,
        pipeline_id: Optional[int],
        alert_type: str,
        severity: str,
        title: str,
        message: str,
    ) -> Dict[str, any]:
        """Send alert.

        Args:
            pipeline_id: Optional pipeline ID.
            alert_type: Alert type (failure, quality, health).
            severity: Alert severity (low, medium, high, critical).
            title: Alert title.
            message: Alert message.

        Returns:
            Dictionary with alert information.
        """
        alert = self.db_manager.add_alert(
            pipeline_id=pipeline_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
        )

        if self._should_send_alert(severity, alert_type):
            self._send_to_channels(alert, severity)

        return {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "sent_at": alert.sent_at,
        }

    def _should_send_alert(self, severity: str, alert_type: str) -> bool:
        """Check if alert should be sent.

        Args:
            severity: Alert severity.
            alert_type: Alert type.

        Returns:
            True if alert should be sent.
        """
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        min_severity = self.alert_rules.get("min_severity", "medium")
        min_level = severity_levels.get(min_severity, 2)

        return severity_levels.get(severity, 0) >= min_level

    def _send_to_channels(self, alert, severity: str) -> None:
        """Send alert to configured channels.

        Args:
            alert: Alert object.
            severity: Alert severity.
        """
        channels = self.alert_channels.get(severity, [])

        for channel in channels:
            channel_type = channel.get("type")

            if channel_type == "email":
                self._send_email(alert, channel)
            elif channel_type == "slack":
                self._send_slack(alert, channel)
            elif channel_type == "webhook":
                self._send_webhook(alert, channel)
            elif channel_type == "log":
                self._log_alert(alert)

    def _send_email(self, alert, channel_config: Dict) -> None:
        """Send email alert.

        Args:
            alert: Alert object.
            channel_config: Channel configuration.
        """
        if not self.alert_channels.get("email_enabled", False):
            return

    def _send_slack(self, alert, channel_config: Dict) -> None:
        """Send Slack alert.

        Args:
            alert: Alert object.
            channel_config: Channel configuration.
        """
        if not self.alert_channels.get("slack_enabled", False):
            return

    def _send_webhook(self, alert, channel_config: Dict) -> None:
        """Send webhook alert.

        Args:
            alert: Alert object.
            channel_config: Channel configuration.
        """
        if not self.alert_channels.get("webhook_enabled", False):
            return

    def _log_alert(self, alert) -> None:
        """Log alert.

        Args:
            alert: Alert object.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"ALERT [{alert.severity.upper()}]: {alert.title} - {alert.message}"
        )

    def alert_on_failure(
        self, pipeline_id: int, failure_type: str, error_message: str, severity: str
    ) -> Dict[str, any]:
        """Send alert for pipeline failure.

        Args:
            pipeline_id: Pipeline ID.
            failure_type: Failure type.
            error_message: Error message.
            severity: Failure severity.

        Returns:
            Dictionary with alert information.
        """
        pipeline = self.db_manager.get_pipeline(pipeline_id)
        pipeline_name = pipeline.name if pipeline else f"Pipeline {pipeline_id}"

        title = f"Pipeline Failure: {pipeline_name}"
        message = f"Failure type: {failure_type}\nError: {error_message}"

        return self.send_alert(
            pipeline_id=pipeline_id,
            alert_type="failure",
            severity=severity,
            title=title,
            message=message,
        )

    def alert_on_quality_issue(
        self,
        pipeline_id: int,
        check_name: str,
        check_result: float,
        threshold: float,
    ) -> Dict[str, any]:
        """Send alert for data quality issue.

        Args:
            pipeline_id: Pipeline ID.
            check_name: Quality check name.
            check_result: Check result value.
            threshold: Threshold value.

        Returns:
            Dictionary with alert information.
        """
        pipeline = self.db_manager.get_pipeline(pipeline_id)
        pipeline_name = pipeline.name if pipeline else f"Pipeline {pipeline_id}"

        severity = "high" if check_result < threshold * 0.5 else "medium"

        title = f"Data Quality Issue: {pipeline_name}"
        message = (
            f"Quality check '{check_name}' failed.\n"
            f"Result: {check_result:.2f}, Threshold: {threshold:.2f}"
        )

        return self.send_alert(
            pipeline_id=pipeline_id,
            alert_type="quality",
            severity=severity,
            title=title,
            message=message,
        )

    def alert_on_health_degradation(
        self, pipeline_id: int, health_status: str, metrics: Dict
    ) -> Dict[str, any]:
        """Send alert for health degradation.

        Args:
            pipeline_id: Pipeline ID.
            health_status: Health status.
            metrics: Health metrics.

        Returns:
            Dictionary with alert information.
        """
        pipeline = self.db_manager.get_pipeline(pipeline_id)
        pipeline_name = pipeline.name if pipeline else f"Pipeline {pipeline_id}"

        severity = "critical" if health_status == "unhealthy" else "high"

        title = f"Pipeline Health Degradation: {pipeline_name}"
        message = (
            f"Pipeline health status: {health_status}\n"
            f"Success rate: {metrics.get('success_rate', 0):.2%}\n"
            f"Failed runs: {metrics.get('failed_runs', 0)}"
        )

        return self.send_alert(
            pipeline_id=pipeline_id,
            alert_type="health",
            severity=severity,
            title=title,
            message=message,
        )

    def get_recent_alerts(
        self,
        pipeline_id: Optional[int] = None,
        severity: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, any]]:
        """Get recent alerts.

        Args:
            pipeline_id: Optional pipeline ID to filter by.
            severity: Optional severity to filter by.
            limit: Maximum number of alerts to return.

        Returns:
            List of alert dictionaries.
        """
        alerts = self.db_manager.get_recent_alerts(
            pipeline_id=pipeline_id, limit=limit
        )

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return [
            {
                "id": alert.id,
                "pipeline_id": alert.pipeline_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "sent_at": alert.sent_at,
                "status": alert.status,
            }
            for alert in alerts
        ]
