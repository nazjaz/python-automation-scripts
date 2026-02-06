"""Generate reports from conversion monitoring data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Website, ConversionRate, DropOffPoint, Recommendation


class ReportGenerator:
    """Generate HTML and CSV reports from conversion monitoring data."""

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
        self, website_id: Optional[int] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            website_id: Optional website ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(website_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(website_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, website_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            website_id: Optional website ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            if website_id:
                website = self.db_manager.get_website(website_id)
                websites = [website] if website else []
            else:
                from src.database import Website

                websites = session.query(Website).all()

            if not websites:
                return None

            website = websites[0]

            conversion_rates = self.db_manager.get_conversion_rates(
                website_id=website.id, hours=168
            )
            dropoffs = self.db_manager.get_dropoff_points(website_id=website.id, limit=10)
            recommendations = self.db_manager.get_recommendations(
                website_id=website.id, limit=10
            )

            from src.conversion_monitor import ConversionMonitor

            monitor = ConversionMonitor(self.db_manager, self.config.get("monitoring", {}))
            conversion_stats = monitor.get_conversion_statistics(website_id=website.id)
            trends = monitor.get_conversion_trends(website_id=website.id, days=7)

            template_path = Path(__file__).parent.parent / "templates" / "conversion_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                website_name=website.website_name or website.domain,
                conversion_stats=conversion_stats,
                trends=trends,
                top_dropoffs=dropoffs[:10],
                top_recommendations=recommendations[:10],
                recent_rates=conversion_rates[:20],
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"conversion_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, website_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            website_id: Optional website ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            if website_id:
                website = self.db_manager.get_website(website_id)
                websites = [website] if website else []
            else:
                from src.database import Website

                websites = session.query(Website).all()

            if not websites:
                return None

            website = websites[0]
            conversion_rates = self.db_manager.get_conversion_rates(
                website_id=website.id, hours=168
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"conversion_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Time Window Start",
                    "Time Window End",
                    "Total Sessions",
                    "Converted Sessions",
                    "Conversion Rate (%)",
                ])

                for rate in conversion_rates:
                    writer.writerow([
                        rate.time_window_start,
                        rate.time_window_end,
                        rate.total_sessions,
                        rate.converted_sessions,
                        rate.conversion_rate,
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
    <title>Conversion Monitoring Report</title>
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
    <h1>Conversion Monitoring Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Conversion Statistics</h2>
    <div class="stat-box">
        <strong>Conversion Rate:</strong> {{ "%.2f"|format(conversion_stats.conversion_rate) }}%
    </div>
    
    <h2>Top Recommendations</h2>
    <table>
        <tr>
            <th>Title</th>
            <th>Priority</th>
            <th>Expected Impact</th>
        </tr>
        {% for rec in top_recommendations %}
        <tr>
            <td>{{ rec.title }}</td>
            <td>{{ rec.priority }}</td>
            <td>{{ "%.2f"|format(rec.expected_impact or 0) }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
