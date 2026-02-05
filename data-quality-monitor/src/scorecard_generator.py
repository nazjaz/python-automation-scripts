"""Generates data quality scorecards and reports."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.integrity_validator import IntegrityIssue
from src.quality_checks import QualityCheckResult
from src.remediation_planner import RemediationPlan

logger = logging.getLogger(__name__)


class Scorecard:
    """Data quality scorecard."""

    def __init__(self, database_name: str, generated_at: Optional[datetime] = None):
        """Initialize scorecard.

        Args:
            database_name: Name of the database.
            generated_at: Timestamp when scorecard was generated.
        """
        self.database_name = database_name
        self.generated_at = generated_at or datetime.utcnow()
        self.table_results: dict[str, dict] = {}
        self.integrity_issues: list[dict] = []
        self.overall_score: float = 0.0
        self.remediation_plans: dict[str, RemediationPlan] = {}

    def add_table_result(
        self, table_name: str, results: list[QualityCheckResult]
    ) -> None:
        """Add quality check results for a table.

        Args:
            table_name: Name of the table.
            results: List of QualityCheckResult objects.
        """
        scores = {}
        passed_checks = 0
        total_checks = len(results)

        for result in results:
            scores[result.check_type] = {
                "score": result.score,
                "passed": result.passed,
                "threshold": result.threshold,
                "issues": result.issues,
            }
            if result.passed:
                passed_checks += 1

        avg_score = sum(r.score for r in results) / total_checks if total_checks > 0 else 0.0

        self.table_results[table_name] = {
            "scores": scores,
            "average_score": avg_score,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
        }

    def add_integrity_issues(self, issues: list[IntegrityIssue]) -> None:
        """Add integrity issues to scorecard.

        Args:
            issues: List of IntegrityIssue objects.
        """
        for issue in issues:
            self.integrity_issues.append(
                {
                    "type": issue.issue_type,
                    "table": issue.table_name,
                    "column": issue.column_name,
                    "description": issue.description,
                    "severity": issue.severity,
                    "affected_rows": issue.affected_rows,
                }
            )

    def calculate_overall_score(self) -> float:
        """Calculate overall data quality score.

        Returns:
            Overall score (0.0 to 1.0).
        """
        if not self.table_results:
            return 0.0

        total_score = sum(
            result["average_score"] for result in self.table_results.values()
        )
        self.overall_score = total_score / len(self.table_results)

        critical_issues = sum(
            1
            for issue in self.integrity_issues
            if issue.get("severity") == "critical"
        )

        if critical_issues > 0:
            self.overall_score *= 0.7

        return self.overall_score

    def to_dict(self) -> dict:
        """Convert scorecard to dictionary.

        Returns:
            Dictionary representation of scorecard.
        """
        return {
            "database_name": self.database_name,
            "generated_at": self.generated_at.isoformat(),
            "overall_score": self.overall_score,
            "table_results": self.table_results,
            "integrity_issues": self.integrity_issues,
            "total_tables": len(self.table_results),
            "total_integrity_issues": len(self.integrity_issues),
        }


class ScorecardGenerator:
    """Generates data quality scorecards in multiple formats."""

    def __init__(self, output_directory: str = "reports", template_path: Optional[str] = None):
        """Initialize scorecard generator.

        Args:
            output_directory: Directory for output files.
            template_path: Path to HTML template directory.
        """
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

        if template_path:
            self.template_env = Environment(
                loader=FileSystemLoader(Path(template_path).parent)
            )
        else:
            template_dir = Path(__file__).parent.parent / "templates"
            self.template_env = Environment(loader=FileSystemLoader(template_dir))

    def generate_json(self, scorecard: Scorecard, filename: Optional[str] = None) -> Path:
        """Generate JSON scorecard.

        Args:
            scorecard: Scorecard object to generate.
            filename: Output filename. If None, auto-generates.

        Returns:
            Path to generated JSON file.
        """
        if filename is None:
            timestamp = scorecard.generated_at.strftime("%Y%m%d_%H%M%S")
            filename = f"scorecard_{scorecard.database_name}_{timestamp}.json"

        output_path = self.output_directory / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scorecard.to_dict(), f, indent=2, default=str)

        logger.info(f"Generated JSON scorecard: {output_path}")
        return output_path

    def generate_html(
        self,
        scorecard: Scorecard,
        filename: Optional[str] = None,
        include_remediation: bool = True,
    ) -> Path:
        """Generate HTML scorecard.

        Args:
            scorecard: Scorecard object to generate.
            filename: Output filename. If None, auto-generates.
            include_remediation: Whether to include remediation plans.

        Returns:
            Path to generated HTML file.
        """
        if filename is None:
            timestamp = scorecard.generated_at.strftime("%Y%m%d_%H%M%S")
            filename = f"scorecard_{scorecard.database_name}_{timestamp}.html"

        output_path = self.output_directory / filename

        try:
            template = self.template_env.get_template("scorecard.html")
        except TemplateNotFound:
            html_content = self._generate_default_html(scorecard, include_remediation)
        else:
            html_content = template.render(
                scorecard=scorecard,
                include_remediation=include_remediation,
                remediation_plans=scorecard.remediation_plans,
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Generated HTML scorecard: {output_path}")
        return output_path

    def generate_excel(
        self, scorecard: Scorecard, filename: Optional[str] = None
    ) -> Path:
        """Generate Excel scorecard.

        Args:
            scorecard: Scorecard object to generate.
            filename: Output filename. If None, auto-generates.

        Returns:
            Path to generated Excel file.
        """
        if filename is None:
            timestamp = scorecard.generated_at.strftime("%Y%m%d_%H%M%S")
            filename = f"scorecard_{scorecard.database_name}_{timestamp}.xlsx"

        output_path = self.output_directory / filename

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            summary_data = {
                "Database": [scorecard.database_name],
                "Overall Score": [scorecard.overall_score],
                "Total Tables": [len(scorecard.table_results)],
                "Integrity Issues": [len(scorecard.integrity_issues)],
                "Generated At": [scorecard.generated_at.isoformat()],
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            table_scores = []
            for table_name, result in scorecard.table_results.items():
                table_scores.append(
                    {
                        "Table": table_name,
                        "Average Score": result["average_score"],
                        "Passed Checks": result["passed_checks"],
                        "Total Checks": result["total_checks"],
                    }
                )
            pd.DataFrame(table_scores).to_excel(
                writer, sheet_name="Table Scores", index=False
            )

            if scorecard.integrity_issues:
                pd.DataFrame(scorecard.integrity_issues).to_excel(
                    writer, sheet_name="Integrity Issues", index=False
                )

        logger.info(f"Generated Excel scorecard: {output_path}")
        return output_path

    def _generate_default_html(
        self, scorecard: Scorecard, include_remediation: bool
    ) -> str:
        """Generate default HTML if template not found.

        Args:
            scorecard: Scorecard object.
            include_remediation: Whether to include remediation.

        Returns:
            HTML content string.
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Quality Scorecard - {scorecard.database_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .score {{ font-size: 2em; font-weight: bold; color: #4a90e2; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4a90e2; color: white; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Data Quality Scorecard</h1>
            <p><strong>Database:</strong> {scorecard.database_name}</p>
            <p><strong>Generated At:</strong> {scorecard.generated_at.isoformat()}</p>
            <p class="score">Overall Score: {scorecard.overall_score:.2%}</p>
            
            <h2>Table Results</h2>
            <table>
                <tr>
                    <th>Table</th>
                    <th>Average Score</th>
                    <th>Passed Checks</th>
                    <th>Total Checks</th>
                </tr>
        """

        for table_name, result in scorecard.table_results.items():
            html += f"""
                <tr>
                    <td>{table_name}</td>
                    <td>{result['average_score']:.2%}</td>
                    <td>{result['passed_checks']}</td>
                    <td>{result['total_checks']}</td>
                </tr>
            """

        html += """
            </table>
        """

        if scorecard.integrity_issues:
            html += """
            <h2>Integrity Issues</h2>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Table</th>
                    <th>Column</th>
                    <th>Severity</th>
                    <th>Description</th>
                </tr>
            """

            for issue in scorecard.integrity_issues:
                html += f"""
                    <tr>
                        <td>{issue['type']}</td>
                        <td>{issue['table']}</td>
                        <td>{issue.get('column', 'N/A')}</td>
                        <td>{issue['severity']}</td>
                        <td>{issue['description']}</td>
                    </tr>
                """

            html += "</table>"

        html += """
        </body>
        </html>
        """

        return html
