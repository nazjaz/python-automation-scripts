"""Generates subscription monitoring reports."""

import csv
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates subscription monitoring reports in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
        output_dir: str = "reports",
    ) -> None:
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
            output_dir: Output directory for reports.
        """
        self.db_manager = db_manager
        self.config = config
        self.reporting_config = config.get("reporting", {})
        self.output_dir = Path(output_dir)

    def generate_html_report(
        self,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML subscription monitoring report.

        Args:
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"subscription_report_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.metrics_tracker import MetricsTracker
        from src.database import Subscription, Customer, ChurnRisk, RetentionCampaign

        tracker = MetricsTracker(self.db_manager, self.config)

        metrics = tracker.track_all_metrics()

        active_subscriptions = (
            self.db_manager.get_session()
            .query(Subscription)
            .filter(Subscription.status == "active")
            .count()
        )

        high_risk_customers = self.db_manager.get_high_risk_customers(risk_level="high", limit=10)

        pending_campaigns = self.db_manager.get_pending_campaigns(limit=10)

        report_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": metrics,
            "active_subscriptions": active_subscriptions,
            "high_risk_customers": [
                {
                    "customer_id": r.customer_id,
                    "risk_score": r.risk_score,
                    "risk_level": r.risk_level,
                    "factors": r.factors,
                }
                for r in high_risk_customers
            ],
            "pending_campaigns": [
                {
                    "customer_id": c.customer_id,
                    "campaign_type": c.campaign_type,
                    "triggered_by": c.triggered_by,
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else "",
                }
                for c in pending_campaigns
            ],
        }

        template_path = Path(__file__).parent.parent / "templates" / "subscription_report.html"
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
            f"Generated HTML report: {output_path}",
            extra={"output_path": str(output_path)},
        )

        return output_path

    def generate_csv_report(
        self,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV subscription monitoring report.

        Args:
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"subscription_report_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.metrics_tracker import MetricsTracker
        from src.database import Subscription

        tracker = MetricsTracker(self.db_manager, self.config)

        metrics = tracker.track_all_metrics()

        subscriptions = (
            self.db_manager.get_session()
            .query(Subscription)
            .all()
        )

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "metric_type",
                "value",
                "date",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for metric_type, value in metrics.items():
                writer.writerow(
                    {
                        "metric_type": metric_type,
                        "value": f"{value:.2f}",
                        "date": date.today().isoformat(),
                    }
                )

        logger.info(
            f"Generated CSV report: {output_path}",
            extra={"output_path": str(output_path)},
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
    <title>Subscription Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f5f5f5;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Subscription Report</h1>
        <p>Generated: {{ generated_at }}</p>
    </div>

    <h2>Metrics</h2>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            {% for metric_type, value in metrics.items() %}
            <tr>
                <td>{{ metric_type|upper }}</td>
                <td>{{ "%.2f"|format(value) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""
