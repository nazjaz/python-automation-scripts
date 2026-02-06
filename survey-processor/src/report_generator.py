"""Generate reports from survey analysis."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Survey, Response, Trend, Insight, Summary


class ReportGenerator:
    """Generate HTML and CSV reports from survey analysis."""

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
        self, survey_id: Optional[int] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            survey_id: Optional survey ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(survey_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(survey_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, survey_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            survey_id: Optional survey ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            if survey_id:
                survey = self.db_manager.get_survey(survey_id)
                surveys = [survey] if survey else []
            else:
                surveys = self.db_manager.get_all_pipelines()

            if not surveys:
                return None

            survey = surveys[0] if surveys else None
            if not survey:
                return None

            responses = self.db_manager.get_survey_responses(survey.id)
            trends = self.db_manager.get_survey_trends(survey.id)
            insights = self.db_manager.get_survey_insights(survey.id, limit=10)
            summary = self.db_manager.get_summary(survey.id)

            from src.satisfaction_calculator import SatisfactionCalculator

            calculator = SatisfactionCalculator(
                self.db_manager, self.config.get("satisfaction", {})
            )
            satisfaction_stats = calculator.get_satisfaction_statistics(survey.id)

            template_path = Path(__file__).parent.parent / "templates" / "survey_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                survey_name=survey.survey_name,
                total_responses=len(responses),
                satisfaction_stats=satisfaction_stats,
                trends=trends[:10],
                insights=insights[:10],
                summary=summary,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"survey_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, survey_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            survey_id: Optional survey ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            if survey_id:
                survey = self.db_manager.get_survey(survey_id)
                if not survey:
                    return None
            else:
                surveys = self.db_manager.get_all_surveys()
                if not surveys:
                    return None
                survey = surveys[0]

            responses = self.db_manager.get_survey_responses(survey.id)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"survey_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Response ID",
                    "Respondent ID",
                    "Respondent Email",
                    "Satisfaction Score",
                    "Submitted At",
                ])

                for response in responses:
                    writer.writerow([
                        response.id,
                        response.respondent_id,
                        response.respondent_email,
                        response.satisfaction_score,
                        response.submitted_at,
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
    <title>Survey Analysis Report</title>
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
    <h1>Survey Analysis Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Responses:</strong> {{ total_responses }}
    </div>
    
    <h2>Key Insights</h2>
    <table>
        <tr>
            <th>Title</th>
            <th>Description</th>
            <th>Priority</th>
        </tr>
        {% for insight in insights %}
        <tr>
            <td>{{ insight.title }}</td>
            <td>{{ insight.description }}</td>
            <td>{{ insight.priority }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
