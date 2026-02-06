"""Generate reports from security monitoring data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, SecurityScan, Vulnerability, ComplianceReport


class ReportGenerator:
    """Generate HTML and CSV reports from security monitoring data."""

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
        self, application_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            application_id: Optional application ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(application_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(application_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, application_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            application_id: Optional application ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            from src.vulnerability_tracker import VulnerabilityTracker
            from src.compliance_reporter import ComplianceReporter
            from src.remediation_timeline import RemediationTimeline
            from src.fix_prioritizer import FixPrioritizer

            tracker = VulnerabilityTracker(
                self.db_manager, self.config.get("vulnerability_tracking", {})
            )
            reporter = ComplianceReporter(
                self.db_manager, self.config.get("compliance", {})
            )
            timeline_gen = RemediationTimeline(
                self.db_manager, self.config.get("remediation", {})
            )
            prioritizer = FixPrioritizer(
                self.db_manager, self.config.get("fix_prioritization", {})
            )

            app_id_int = None
            if application_id:
                application = self.db_manager.get_application(application_id)
                if application:
                    app_id_int = application.id

            vulnerability_stats = tracker.get_vulnerability_statistics(
                application_id=app_id_int
            )
            critical_vulns = tracker.get_critical_vulnerabilities(
                application_id=app_id_int, limit=10
            )
            overdue_vulns = tracker.get_overdue_vulnerabilities(
                application_id=app_id_int
            )
            prioritized_fixes = prioritizer.get_prioritized_fixes(
                application_id=app_id_int, limit=10
            )

            compliance_trends = None
            if app_id_int:
                compliance_trends = reporter.get_compliance_trends(
                    application_id=app_id_int, days=30
                )

            timeline_summary = timeline_gen.get_timeline_summary(
                application_id=app_id_int
            )
            upcoming_deadlines = timeline_gen.get_upcoming_deadlines(
                days=7, application_id=app_id_int
            )

            template_path = Path(__file__).parent.parent / "templates" / "security_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                vulnerability_stats=vulnerability_stats,
                critical_vulnerabilities=critical_vulns,
                overdue_vulnerabilities=overdue_vulns,
                prioritized_fixes=prioritized_fixes,
                compliance_trends=compliance_trends,
                timeline_summary=timeline_summary,
                upcoming_deadlines=upcoming_deadlines,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"security_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, application_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            application_id: Optional application ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            app_id_int = None
            if application_id:
                application = self.db_manager.get_application(application_id)
                if application:
                    app_id_int = application.id

            vulnerabilities = self.db_manager.get_open_vulnerabilities(
                application_id=app_id_int, limit=100
            )

            if not vulnerabilities:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"security_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Vulnerability ID",
                    "Title",
                    "Severity",
                    "CVSS Score",
                    "CVE ID",
                    "Status",
                    "Component",
                    "Discovered At",
                ])

                for vuln in vulnerabilities:
                    writer.writerow([
                        vuln.vulnerability_id,
                        vuln.title,
                        vuln.severity,
                        vuln.cvss_score,
                        vuln.cve_id,
                        vuln.status,
                        vuln.component,
                        vuln.discovered_at,
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
    <title>Security Monitoring Report</title>
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
    <h1>Security Monitoring Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Vulnerabilities:</strong> {{ vulnerability_stats.total_vulnerabilities }}
    </div>
    
    <h2>Critical Vulnerabilities</h2>
    <table>
        <tr>
            <th>Vulnerability ID</th>
            <th>Title</th>
            <th>CVSS Score</th>
        </tr>
        {% for vuln in critical_vulnerabilities %}
        <tr>
            <td>{{ vuln.vulnerability_id }}</td>
            <td>{{ vuln.title }}</td>
            <td>{{ vuln.cvss_score }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
