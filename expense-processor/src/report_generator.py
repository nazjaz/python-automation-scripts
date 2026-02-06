"""Generates expense reports in various formats."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates expense reports in various formats."""

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
        report_id: int,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML expense report.

        Args:
            report_id: Report ID.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"expense_report_{report_id}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.database import ExpenseReport, Expense, Receipt, Employee

        report = (
            self.db_manager.get_session()
            .query(ExpenseReport)
            .filter(ExpenseReport.id == report_id)
            .first()
        )

        if not report:
            raise ValueError(f"Report {report_id} not found")

        employee = (
            self.db_manager.get_session()
            .query(Employee)
            .filter(Employee.id == report.employee_id)
            .first()
        )

        report_data = {
            "report_id": report.id,
            "employee_name": employee.name if employee else "Unknown",
            "employee_email": employee.email if employee else "",
            "report_date": report.report_date.isoformat(),
            "submission_date": report.submission_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": report.status,
            "total_amount": report.total_amount,
            "reimbursable_amount": report.reimbursable_amount,
            "currency": report.currency,
            "description": report.description or "",
            "expenses": [],
        }

        for expense in report.expenses:
            receipts = [
                {
                    "file_path": r.file_path,
                    "extracted_amount": r.extracted_amount,
                    "extracted_merchant": r.extracted_merchant,
                }
                for r in expense.receipts
            ]

            report_data["expenses"].append(
                {
                    "id": expense.id,
                    "date": expense.expense_date.isoformat(),
                    "category": expense.category,
                    "amount": expense.amount,
                    "merchant": expense.merchant or "",
                    "description": expense.description or "",
                    "validated": expense.validated,
                    "validation_notes": expense.validation_notes or "",
                    "receipts": receipts,
                }
            )

        template_path = Path(__file__).parent.parent / "templates" / "expense_report.html"
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
            extra={"output_path": str(output_path), "report_id": report_id},
        )

        return output_path

    def generate_csv_report(
        self,
        report_id: int,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV expense report.

        Args:
            report_id: Report ID.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"expense_report_{report_id}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.database import ExpenseReport, Expense, Employee

        report = (
            self.db_manager.get_session()
            .query(ExpenseReport)
            .filter(ExpenseReport.id == report_id)
            .first()
        )

        if not report:
            raise ValueError(f"Report {report_id} not found")

        employee = (
            self.db_manager.get_session()
            .query(Employee)
            .filter(Employee.id == report.employee_id)
            .first()
        )

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "expense_id",
                "date",
                "category",
                "merchant",
                "amount",
                "currency",
                "description",
                "validated",
                "validation_notes",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            writer.writerow(
                {
                    "expense_id": "REPORT",
                    "date": report.report_date.isoformat(),
                    "category": "SUMMARY",
                    "merchant": employee.name if employee else "",
                    "amount": report.total_amount,
                    "currency": report.currency,
                    "description": f"Total: ${report.total_amount:.2f}, Reimbursable: ${report.reimbursable_amount:.2f}",
                    "validated": "",
                    "validation_notes": "",
                }
            )

            for expense in report.expenses:
                writer.writerow(
                    {
                        "expense_id": expense.id,
                        "date": expense.expense_date.isoformat(),
                        "category": expense.category,
                        "merchant": expense.merchant or "",
                        "amount": expense.amount,
                        "currency": expense.currency,
                        "description": expense.description or "",
                        "validated": "Yes" if expense.validated else "No",
                        "validation_notes": expense.validation_notes or "",
                    }
                )

        logger.info(
            f"Generated CSV report: {output_path}",
            extra={"output_path": str(output_path), "report_id": report_id},
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
    <title>Expense Report</title>
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
        .summary {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Expense Report</h1>
        <p>Employee: {{ employee_name }} ({{ employee_email }})</p>
        <p>Report Date: {{ report_date }} | Status: {{ status }}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Amount:</strong> ${{ "%.2f"|format(total_amount) }} {{ currency }}</p>
        <p><strong>Reimbursable Amount:</strong> ${{ "%.2f"|format(reimbursable_amount) }} {{ currency }}</p>
    </div>

    <h2>Expenses</h2>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Merchant</th>
                <th>Amount</th>
                <th>Description</th>
                <th>Validated</th>
            </tr>
        </thead>
        <tbody>
            {% for expense in expenses %}
            <tr>
                <td>{{ expense.date }}</td>
                <td>{{ expense.category }}</td>
                <td>{{ expense.merchant }}</td>
                <td>${{ "%.2f"|format(expense.amount) }}</td>
                <td>{{ expense.description }}</td>
                <td>{{ "Yes" if expense.validated else "No" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""
