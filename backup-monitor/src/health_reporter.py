"""Generates backup health reports."""

import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, BackupLocation, HealthMetric

logger = logging.getLogger(__name__)


class HealthReporter:
    """Generates backup health reports in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        output_dir: str = "reports",
    ) -> None:
        """Initialize health reporter.

        Args:
            db_manager: Database manager instance.
            output_dir: Output directory for reports.
        """
        self.db_manager = db_manager
        self.output_dir = Path(output_dir)

    def calculate_health_score(
        self,
        location_id: int,
        days: int = 7,
    ) -> float:
        """Calculate health score for backup location.

        Args:
            location_id: Location ID.
            days: Number of days to analyze.

        Returns:
            Health score (0.0 to 1.0).
        """
        from src.backup_monitor import BackupMonitor
        from src.database import BackupVerification, RestoreTest

        monitor = BackupMonitor(self.db_manager, {})
        health_data = monitor.check_backup_health(location_id=location_id, days=days)

        if not health_data:
            return 0.0

        location = self.db_manager.get_session().query(BackupLocation).filter(BackupLocation.id == location_id).first()
        if not location:
            return 0.0

        location_name = location.name
        data = health_data.get(location_name, {})

        success_rate = data.get("success_rate", 0.0)

        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            verifications = (
                session.query(BackupVerification)
                .join(Backup)
                .filter(Backup.location_id == location_id)
                .filter(BackupVerification.verified_at >= cutoff_date)
                .all()
            )

            restore_tests = (
                session.query(RestoreTest)
                .join(Backup)
                .filter(Backup.location_id == location_id)
                .filter(RestoreTest.tested_at >= cutoff_date)
                .all()
            )

            verification_success_rate = 0.0
            if verifications:
                successful = len([v for v in verifications if v.status == "passed"])
                verification_success_rate = successful / len(verifications)

            restore_success_rate = 0.0
            if restore_tests:
                successful = len([t for t in restore_tests if t.status == "passed"])
                restore_success_rate = successful / len(restore_tests)

            health_score = (
                success_rate * 0.5
                + verification_success_rate * 0.3
                + restore_success_rate * 0.2
            )

            return round(health_score, 4)
        finally:
            session.close()

    def generate_health_metrics(
        self,
        location_id: Optional[int] = None,
        days: int = 7,
    ) -> List[HealthMetric]:
        """Generate health metrics for location(s).

        Args:
            location_id: Optional location ID filter.
            days: Number of days to analyze.

        Returns:
            List of HealthMetric objects.
        """
        from src.backup_monitor import BackupMonitor

        monitor = BackupMonitor(self.db_manager, {})

        if location_id:
            locations = [self.db_manager.get_session().query(BackupLocation).filter(BackupLocation.id == location_id).first()]
            locations = [l for l in locations if l]
        else:
            locations = self.db_manager.get_backup_locations(enabled_only=True)

        metrics = []

        for location in locations:
            health_data = monitor.check_backup_health(location_id=location.id, days=days)
            location_name = location.name
            data = health_data.get(location_name, {})

            health_score = self.calculate_health_score(location.id, days=days)

            metric = self.db_manager.add_health_metric(
                location_id=location.id,
                metric_date=datetime.utcnow(),
                total_backups=data.get("total_backups", 0),
                successful_backups=data.get("successful_backups", 0),
                failed_backups=data.get("failed_backups", 0),
                total_size_bytes=data.get("total_size_bytes", 0),
                verification_success_rate=None,
                restore_test_success_rate=None,
                health_score=health_score,
            )

            metrics.append(metric)

        return metrics

    def generate_html_report(
        self,
        location_id: Optional[int] = None,
        days: int = 7,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML health report.

        Args:
            location_id: Optional location ID filter.
            days: Number of days to analyze.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            location_suffix = f"_{location_id}" if location_id else ""
            filename = f"backup_health_report{location_suffix}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.backup_monitor import BackupMonitor

        monitor = BackupMonitor(self.db_manager, {})
        health_data = monitor.check_backup_health(location_id=location_id, days=days)

        locations = self.db_manager.get_backup_locations(enabled_only=True)
        if location_id:
            locations = [l for l in locations if l.id == location_id]

        report_data = {
            "locations": [],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "days": days,
        }

        for location in locations:
            location_health = health_data.get(location.name, {})
            health_score = self.calculate_health_score(location.id, days=days)

            report_data["locations"].append(
                {
                    "name": location.name,
                    "path": location.path,
                    "type": location.backup_type,
                    "total_backups": location_health.get("total_backups", 0),
                    "successful_backups": location_health.get("successful_backups", 0),
                    "failed_backups": location_health.get("failed_backups", 0),
                    "success_rate": location_health.get("success_rate", 0.0),
                    "total_size_gb": location_health.get("total_size_bytes", 0) / (1024 ** 3),
                    "health_score": health_score,
                }
            )

        template_path = Path(__file__).parent.parent / "templates" / "health_report.html"
        if not template_path.exists():
            html_content = self._get_default_html_template()
        else:
            with open(template_path, "r") as f:
                html_content = f.read()

        template = Template(html_content)
        rendered_html = template.render(**report_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logger.info(
            f"Generated HTML health report: {output_path}",
            extra={"output_path": str(output_path), "location_id": location_id},
        )

        return output_path

    def generate_csv_report(
        self,
        location_id: Optional[int] = None,
        days: int = 7,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV health report.

        Args:
            location_id: Optional location ID filter.
            days: Number of days to analyze.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            location_suffix = f"_{location_id}" if location_id else ""
            filename = f"backup_health_report{location_suffix}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.backup_monitor import BackupMonitor

        monitor = BackupMonitor(self.db_manager, {})
        health_data = monitor.check_backup_health(location_id=location_id, days=days)

        locations = self.db_manager.get_backup_locations(enabled_only=True)
        if location_id:
            locations = [l for l in locations if l.id == location_id]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "location_name",
                "path",
                "type",
                "total_backups",
                "successful_backups",
                "failed_backups",
                "success_rate",
                "total_size_gb",
                "health_score",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for location in locations:
                location_health = health_data.get(location.name, {})
                health_score = self.calculate_health_score(location.id, days=days)

                writer.writerow(
                    {
                        "location_name": location.name,
                        "path": location.path,
                        "type": location.backup_type,
                        "total_backups": location_health.get("total_backups", 0),
                        "successful_backups": location_health.get("successful_backups", 0),
                        "failed_backups": location_health.get("failed_backups", 0),
                        "success_rate": f"{location_health.get('success_rate', 0.0):.2%}",
                        "total_size_gb": f"{location_health.get('total_size_bytes', 0) / (1024 ** 3):.2f}",
                        "health_score": f"{health_score:.4f}",
                    }
                )

        logger.info(
            f"Generated CSV health report: {output_path}",
            extra={"output_path": str(output_path), "location_id": location_id},
        )

        return output_path

    def _get_default_html_template(self) -> str:
        """Get default HTML template for reports.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backup Health Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .location {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .location h2 {
            color: #667eea;
            margin-top: 0;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .metric {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
        }
        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .health-score {
            font-size: 2em;
            font-weight: bold;
        }
        .health-score.good {
            color: #28a745;
        }
        .health-score.warning {
            color: #ffc107;
        }
        .health-score.critical {
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Backup Health Report</h1>
        <p>Generated on {{ generated_at }} - Last {{ days }} days</p>
    </div>

    {% for location in locations %}
    <div class="location">
        <h2>{{ location.name }}</h2>
        <p><strong>Path:</strong> {{ location.path }} | <strong>Type:</strong> {{ location.type }}</p>
        <div class="metrics">
            <div class="metric">
                <div class="metric-label">Total Backups</div>
                <div class="metric-value">{{ location.total_backups }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Successful</div>
                <div class="metric-value">{{ location.successful_backups }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Failed</div>
                <div class="metric-value">{{ location.failed_backups }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{{ "%.1f"|format(location.success_rate * 100) }}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Size</div>
                <div class="metric-value">{{ "%.2f"|format(location.total_size_gb) }} GB</div>
            </div>
            <div class="metric">
                <div class="metric-label">Health Score</div>
                <div class="health-score {% if location.health_score >= 0.8 %}good{% elif location.health_score >= 0.5 %}warning{% else %}critical{% endif %}">
                    {{ "%.1f"|format(location.health_score * 100) }}%
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</body>
</html>"""
