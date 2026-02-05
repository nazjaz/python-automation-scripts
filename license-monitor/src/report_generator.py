"""License monitoring report generation service."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.database import (
    DatabaseManager,
    ComplianceRecord,
    License,
    OptimizationRecommendation,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates license monitoring reports in multiple formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        output_directory: str = "reports",
        template_path: Optional[str] = None,
    ):
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            output_directory: Directory for output files.
            template_path: Path to HTML template directory.
        """
        self.db_manager = db_manager
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

        if template_path:
            self.template_env = Environment(
                loader=FileSystemLoader(Path(template_path).parent)
            )
        else:
            template_dir = Path(__file__).parent.parent / "templates"
            self.template_env = Environment(loader=FileSystemLoader(template_dir))

    def generate_json(
        self,
        compliance_records: list[ComplianceRecord],
        recommendations: list[OptimizationRecommendation],
        filename: Optional[str] = None,
    ) -> Path:
        """Generate JSON report.

        Args:
            compliance_records: List of compliance records.
            recommendations: List of optimization recommendations.
            filename: Output filename. If None, auto-generates.

        Returns:
            Path to generated JSON file.
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"license_report_{timestamp}.json"

        output_path = self.output_directory / filename

        report_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "compliance": [
                {
                    "license_type": r.license_type,
                    "total_licenses": r.total_licenses,
                    "assigned_licenses": r.assigned_licenses,
                    "unused_licenses": r.unused_licenses,
                    "compliance_percentage": r.compliance_percentage,
                    "status": r.status,
                    "check_date": r.check_date.isoformat(),
                }
                for r in compliance_records
            ],
            "optimization_recommendations": [
                {
                    "license_type": r.license_type,
                    "type": r.recommendation_type,
                    "description": r.description,
                    "estimated_savings": r.estimated_savings,
                    "currency": r.currency,
                    "priority": r.priority,
                }
                for r in recommendations
            ],
            "total_potential_savings": sum(r.estimated_savings for r in recommendations),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Generated JSON report: {output_path}")
        return output_path

    def generate_html(
        self,
        compliance_records: list[ComplianceRecord],
        recommendations: list[OptimizationRecommendation],
        filename: Optional[str] = None,
    ) -> Path:
        """Generate HTML report.

        Args:
            compliance_records: List of compliance records.
            recommendations: List of optimization recommendations.
            filename: Output filename. If None, auto-generates.

        Returns:
            Path to generated HTML file.
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"license_report_{timestamp}.html"

        output_path = self.output_directory / filename

        total_savings = sum(r.estimated_savings for r in recommendations)

        try:
            template = self.template_env.get_template("license_report.html")
            html_content = template.render(
                generated_at=datetime.utcnow(),
                compliance_records=compliance_records,
                recommendations=recommendations,
                total_savings=total_savings,
            )
        except TemplateNotFound:
            html_content = self._generate_default_html(
                compliance_records, recommendations, total_savings
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Generated HTML report: {output_path}")
        return output_path

    def generate_excel(
        self,
        compliance_records: list[ComplianceRecord],
        recommendations: list[OptimizationRecommendation],
        filename: Optional[str] = None,
    ) -> Path:
        """Generate Excel report.

        Args:
            compliance_records: List of compliance records.
            recommendations: List of optimization recommendations.
            filename: Output filename. If None, auto-generates.

        Returns:
            Path to generated Excel file.
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"license_report_{timestamp}.xlsx"

        output_path = self.output_directory / filename

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            compliance_data = [
                {
                    "License Type": r.license_type,
                    "Total Licenses": r.total_licenses,
                    "Assigned": r.assigned_licenses,
                    "Unused": r.unused_licenses,
                    "Compliance %": r.compliance_percentage,
                    "Status": r.status,
                    "Check Date": r.check_date.isoformat(),
                }
                for r in compliance_records
            ]
            pd.DataFrame(compliance_data).to_excel(
                writer, sheet_name="Compliance", index=False
            )

            recommendations_data = [
                {
                    "License Type": r.license_type,
                    "Type": r.recommendation_type,
                    "Description": r.description,
                    "Estimated Savings": r.estimated_savings,
                    "Currency": r.currency,
                    "Priority": r.priority,
                }
                for r in recommendations
            ]
            pd.DataFrame(recommendations_data).to_excel(
                writer, sheet_name="Optimization", index=False
            )

        logger.info(f"Generated Excel report: {output_path}")
        return output_path

    def _generate_default_html(
        self,
        compliance_records: list[ComplianceRecord],
        recommendations: list[OptimizationRecommendation],
        total_savings: float,
    ) -> str:
        """Generate default HTML if template not found.

        Args:
            compliance_records: List of compliance records.
            recommendations: List of optimization recommendations.
            total_savings: Total potential savings.

        Returns:
            HTML content string.
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>License Monitoring Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4a90e2; color: white; }}
                .savings {{ font-size: 1.5em; color: #28a745; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>License Monitoring Report</h1>
            <p>Generated: {datetime.utcnow().isoformat()}</p>
            
            <h2>Compliance Status</h2>
            <table>
                <tr>
                    <th>License Type</th>
                    <th>Total</th>
                    <th>Assigned</th>
                    <th>Unused</th>
                    <th>Compliance %</th>
                    <th>Status</th>
                </tr>
        """

        for record in compliance_records:
            html += f"""
                <tr>
                    <td>{record.license_type}</td>
                    <td>{record.total_licenses}</td>
                    <td>{record.assigned_licenses}</td>
                    <td>{record.unused_licenses}</td>
                    <td>{record.compliance_percentage:.2%}</td>
                    <td>{record.status}</td>
                </tr>
            """

        html += """
            </table>
        """

        if recommendations:
            html += f"""
            <h2>Optimization Recommendations</h2>
            <p class="savings">Total Potential Savings: ${total_savings:.2f}</p>
            <table>
                <tr>
                    <th>License Type</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th>Estimated Savings</th>
                    <th>Priority</th>
                </tr>
            """

            for rec in recommendations:
                html += f"""
                    <tr>
                        <td>{rec.license_type}</td>
                        <td>{rec.recommendation_type}</td>
                        <td>{rec.description}</td>
                        <td>${rec.estimated_savings:.2f}</td>
                        <td>{rec.priority}</td>
                    </tr>
                """

            html += "</table>"

        html += """
        </body>
        </html>
        """

        return html
