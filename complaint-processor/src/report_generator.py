"""Generate reports from complaint processing data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Complaint, Resolution, FollowUp


class ReportGenerator:
    """Generate HTML and CSV reports from complaint processing data."""

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
        self, complaint_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            complaint_id: Optional complaint ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(complaint_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(complaint_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, complaint_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            complaint_id: Optional complaint ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            from src.resolution_tracker import ResolutionTracker
            from src.issue_categorizer import IssueCategorizer

            tracker = ResolutionTracker(
                self.db_manager, self.config.get("resolution_tracking", {})
            )
            categorizer = IssueCategorizer(
                self.db_manager, self.config.get("categorization", {})
            )

            if complaint_id:
                complaint = self.db_manager.get_complaint(complaint_id)
                complaints = [complaint] if complaint else []
            else:
                complaints = self.db_manager.get_open_complaints(limit=20)

            if not complaints:
                return None

            resolution_stats = tracker.get_resolution_statistics(days=30)
            category_stats = categorizer.get_category_statistics()

            resolved_complaints = [
                c for c in complaints if c.status == "resolved"
            ][:10]

            template_path = Path(__file__).parent.parent / "templates" / "complaint_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                resolution_stats=resolution_stats,
                category_stats=category_stats,
                open_complaints=complaints[:10],
                resolved_complaints=resolved_complaints[:10],
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"complaint_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, complaint_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            complaint_id: Optional complaint ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            if complaint_id:
                complaint = self.db_manager.get_complaint(complaint_id)
                complaints = [complaint] if complaint else []
            else:
                complaints = self.db_manager.get_open_complaints(limit=100)

            if not complaints:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"complaint_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Complaint ID",
                    "Customer ID",
                    "Category",
                    "Priority",
                    "Status",
                    "Department",
                    "Created At",
                    "Resolved At",
                ])

                for complaint in complaints:
                    writer.writerow([
                        complaint.complaint_id,
                        complaint.customer.customer_id if complaint.customer else "N/A",
                        complaint.category,
                        complaint.priority,
                        complaint.status,
                        complaint.department.department_name if complaint.department else "N/A",
                        complaint.created_at,
                        complaint.resolved_at,
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
    <title>Complaint Processing Report</title>
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
    <h1>Complaint Processing Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Complaints:</strong> {{ resolution_stats.total_complaints }}
    </div>
    
    <h2>Open Complaints</h2>
    <table>
        <tr>
            <th>Complaint ID</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
        </tr>
        {% for complaint in open_complaints %}
        <tr>
            <td>{{ complaint.complaint_id }}</td>
            <td>{{ complaint.category }}</td>
            <td>{{ complaint.priority }}</td>
            <td>{{ complaint.status }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
