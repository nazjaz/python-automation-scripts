"""Generate reports from error analysis."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, ErrorLog, BugReport, ErrorPattern


class ReportGenerator:
    """Generate HTML and CSV reports from error analysis."""

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
        self, application: Optional[str] = None, environment: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            application: Optional application to filter by.
            environment: Optional environment to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(application, environment)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(application, environment)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, application: Optional[str] = None, environment: Optional[str] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            application: Optional application to filter by.
            environment: Optional environment to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(ErrorLog)
            if application:
                query = query.filter(ErrorLog.application == application)
            if environment:
                query = query.filter(ErrorLog.environment == environment)

            errors = query.order_by(ErrorLog.timestamp.desc()).limit(100).all()
            bug_reports = session.query(BugReport).order_by(BugReport.created_at.desc()).limit(20).all()
            patterns = session.query(ErrorPattern).order_by(ErrorPattern.frequency.desc()).limit(20).all()

            if not errors and not bug_reports:
                return None

            error_stats = self._calculate_error_statistics(errors)
            pattern_stats = self._calculate_pattern_statistics(patterns)

            template_path = Path(__file__).parent.parent / "templates" / "error_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_errors=len(errors),
                error_stats=error_stats,
                pattern_stats=pattern_stats,
                top_patterns=patterns[:10],
                top_bug_reports=bug_reports[:10],
                recent_errors=errors[:50],
                application=application,
                environment=environment,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"error_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, application: Optional[str] = None, environment: Optional[str] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            application: Optional application to filter by.
            environment: Optional environment to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(ErrorLog)
            if application:
                query = query.filter(ErrorLog.application == application)
            if environment:
                query = query.filter(ErrorLog.environment == environment)

            errors = query.order_by(ErrorLog.timestamp.desc()).limit(1000).all()

            if not errors:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"error_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Error ID",
                    "Timestamp",
                    "Application",
                    "Environment",
                    "Error Type",
                    "Severity",
                    "Category",
                    "Error Message",
                    "User ID",
                    "Request ID",
                ])

                for error in errors:
                    writer.writerow([
                        error.id,
                        error.timestamp,
                        error.application,
                        error.environment,
                        error.error_type,
                        error.severity,
                        error.category.name if error.category else "",
                        error.error_message[:200] + "..." if len(error.error_message) > 200 else error.error_message,
                        error.user_id,
                        error.request_id,
                    ])

            return output_path
        finally:
            session.close()

    def _calculate_error_statistics(self, errors: List[ErrorLog]) -> Dict[str, any]:
        """Calculate error statistics.

        Args:
            errors: List of error log objects.

        Returns:
            Error statistics dictionary.
        """
        if not errors:
            return {
                "total_errors": 0,
                "by_severity": {},
                "by_category": {},
                "by_application": {},
            }

        from collections import Counter

        severity_counts = Counter(e.severity for e in errors if e.severity)
        category_counts = Counter(e.category.name for e in errors if e.category)
        application_counts = Counter(e.application for e in errors if e.application)

        return {
            "total_errors": len(errors),
            "by_severity": dict(severity_counts),
            "by_category": dict(category_counts),
            "by_application": dict(application_counts),
        }

    def _calculate_pattern_statistics(self, patterns: List[ErrorPattern]) -> Dict[str, any]:
        """Calculate pattern statistics.

        Args:
            patterns: List of error pattern objects.

        Returns:
            Pattern statistics dictionary.
        """
        if not patterns:
            return {
                "total_patterns": 0,
                "total_frequency": 0,
                "by_trend": {},
            }

        from collections import Counter

        trend_counts = Counter(p.trend for p in patterns if p.trend)
        total_frequency = sum(p.frequency for p in patterns)

        return {
            "total_patterns": len(patterns),
            "total_frequency": total_frequency,
            "by_trend": dict(trend_counts),
        }

    def _get_default_html_template(self) -> str:
        """Get default HTML template.

        Returns:
            Default HTML template string.
        """
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Error Analysis Report</title>
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
    <h1>Error Analysis Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Errors:</strong> {{ total_errors }}
    </div>
    
    <h2>Top Bug Reports</h2>
    <table>
        <tr>
            <th>Title</th>
            <th>Priority</th>
            <th>Severity</th>
            <th>Status</th>
        </tr>
        {% for report in top_bug_reports %}
        <tr>
            <td>{{ report.title }}</td>
            <td>{{ report.priority }}</td>
            <td>{{ report.severity }}</td>
            <td>{{ report.status }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
