"""Generate logistics reports."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Shipment, LogisticsMetric, OptimizationRecommendation


class ReportGenerator:
    """Generate HTML and CSV reports from logistics data."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.output_dir = Path(config.get("output_directory", "reports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_reports(
        self, shipment_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            shipment_id: Optional shipment ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(shipment_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(shipment_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, shipment_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            shipment_id: Optional shipment ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            from src.logistics_monitor import LogisticsMonitor
            from src.delay_predictor import DelayPredictor

            monitor = LogisticsMonitor(self.db_manager, self.config.get("monitoring", {}))
            delay_predictor = DelayPredictor(
                self.db_manager, self.config.get("delay_prediction", {})
            )

            logistics_summary = monitor.monitor_logistics(days=7)
            trends = monitor.get_logistics_trends(days=30)
            delay_stats = delay_predictor.get_delay_statistics(days=30)

            active_shipments = self.db_manager.get_active_shipments(limit=20)
            recommendations = self.db_manager.get_optimization_recommendations(limit=10)

            if shipment_id:
                shipment = self.db_manager.get_shipment(shipment_id)
                shipments = [shipment] if shipment else []
            else:
                shipments = active_shipments[:10]

            template_path = Path(__file__).parent.parent / "templates" / "logistics_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                logistics_summary=logistics_summary,
                trends=trends,
                delay_stats=delay_stats,
                active_shipments=shipments,
                recommendations=recommendations,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"logistics_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, shipment_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            shipment_id: Optional shipment ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            if shipment_id:
                shipment = self.db_manager.get_shipment(shipment_id)
                shipments = [shipment] if shipment else []
            else:
                shipments = self.db_manager.get_active_shipments(limit=100)

            if not shipments:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"logistics_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Shipment ID",
                    "Status",
                    "Origin",
                    "Destination",
                    "Estimated Delivery",
                    "Actual Delivery",
                    "Priority",
                ])

                for shipment in shipments:
                    writer.writerow([
                        shipment.shipment_id,
                        shipment.status,
                        shipment.origin,
                        shipment.destination,
                        shipment.estimated_delivery,
                        shipment.actual_delivery,
                        shipment.priority,
                    ])

            return output_path
        finally:
            session.close()

    def _get_default_html_template(self) -> str:
        """Get default HTML template.

        Returns:
            Default HTML template string.
        """
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Logistics Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .stat-box { display: inline-block; margin: 10px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Logistics Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Shipments:</strong> {{ logistics_summary.total_shipments }}
    </div>
    
    <h2>Active Shipments</h2>
    <table>
        <tr>
            <th>Shipment ID</th>
            <th>Status</th>
            <th>Origin</th>
            <th>Destination</th>
        </tr>
        {% for shipment in active_shipments %}
        <tr>
            <td>{{ shipment.shipment_id }}</td>
            <td>{{ shipment.status }}</td>
            <td>{{ shipment.origin }}</td>
            <td>{{ shipment.destination }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
