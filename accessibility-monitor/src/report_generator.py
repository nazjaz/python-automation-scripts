"""Generates accessibility compliance reports."""

import csv
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates accessibility compliance reports in various formats."""

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
        website_id: Optional[int] = None,
        scan_id: Optional[int] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML accessibility report.

        Args:
            website_id: Optional website ID filter.
            scan_id: Optional scan ID filter.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_scan{scan_id}" if scan_id else f"_website{website_id}" if website_id else ""
            filename = f"accessibility_report{suffix}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.remediation_generator import RemediationGenerator
        from src.progress_tracker import ProgressTracker

        remediation_gen = RemediationGenerator(self.db_manager, self.config)
        progress_tracker = ProgressTracker(self.db_manager, self.config)

        if scan_id:
            from src.database import AccessibilityScan
            scan = self.db_manager.get_session().query(AccessibilityScan).filter_by(id=scan_id).first()
            scans = [scan] if scan else []
            violations = self.db_manager.get_violations(scan_id=scan_id)
        elif website_id:
            scans = self.db_manager.get_scans(website_id=website_id, limit=10)
            violations = []
            for scan in scans:
                violations.extend(self.db_manager.get_violations(scan_id=scan.id))
        else:
            scans = self.db_manager.get_scans(limit=10)
            violations = self.db_manager.get_violations(limit=100)

        remediation_summary = remediation_gen.get_remediation_summary(
            website_id=website_id, scan_id=scan_id
        )

        progress_trend = None
        if website_id:
            progress_trend = progress_tracker.get_progress_trend(website_id, days=30)

        report_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scans": [
                {
                    "id": s.id,
                    "page_url": s.page_url,
                    "scan_date": s.scan_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "compliance_score": s.compliance_score,
                    "total_violations": s.total_violations,
                    "critical_violations": s.critical_violations,
                    "high_violations": s.high_violations,
                }
                for s in scans
            ],
            "violations": [
                {
                    "wcag_criterion": v.wcag_criterion,
                    "severity": v.severity,
                    "violation_type": v.violation_type,
                    "description": v.description,
                    "recommendation": v.recommendation,
                }
                for v in violations[:50]
            ],
            "remediation_summary": remediation_summary,
            "progress_trend": progress_trend,
        }

        template_path = Path(__file__).parent.parent / "templates" / "accessibility_report.html"
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
            extra={"output_path": str(output_path), "website_id": website_id, "scan_id": scan_id},
        )

        return output_path

    def generate_csv_report(
        self,
        website_id: Optional[int] = None,
        scan_id: Optional[int] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV accessibility report.

        Args:
            website_id: Optional website ID filter.
            scan_id: Optional scan ID filter.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_scan{scan_id}" if scan_id else f"_website{website_id}" if website_id else ""
            filename = f"accessibility_report{suffix}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if scan_id:
            violations = self.db_manager.get_violations(scan_id=scan_id)
        elif website_id:
            scans = self.db_manager.get_scans(website_id=website_id)
            violations = []
            for scan in scans:
                violations.extend(self.db_manager.get_violations(scan_id=scan.id))
        else:
            violations = self.db_manager.get_violations(limit=1000)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "wcag_criterion",
                "severity",
                "violation_type",
                "description",
                "element_type",
                "element_selector",
                "recommendation",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for violation in violations:
                writer.writerow(
                    {
                        "wcag_criterion": violation.wcag_criterion,
                        "severity": violation.severity,
                        "violation_type": violation.violation_type,
                        "description": violation.description,
                        "element_type": violation.element_type or "",
                        "element_selector": violation.element_selector or "",
                        "recommendation": violation.recommendation or "",
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
    <title>Accessibility Compliance Report</title>
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
        .severity-critical { color: #dc3545; font-weight: bold; }
        .severity-high { color: #f39c12; font-weight: bold; }
        .severity-medium { color: #ffc107; }
        .severity-low { color: #28a745; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Accessibility Compliance Report</h1>
        <p>Generated: {{ generated_at }}</p>
    </div>

    <h2>Violations</h2>
    <table>
        <thead>
            <tr>
                <th>WCAG Criterion</th>
                <th>Severity</th>
                <th>Type</th>
                <th>Description</th>
                <th>Recommendation</th>
            </tr>
        </thead>
        <tbody>
            {% for violation in violations %}
            <tr>
                <td>{{ violation.wcag_criterion }}</td>
                <td class="severity-{{ violation.severity }}">{{ violation.severity }}</td>
                <td>{{ violation.violation_type }}</td>
                <td>{{ violation.description }}</td>
                <td>{{ violation.recommendation }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""
