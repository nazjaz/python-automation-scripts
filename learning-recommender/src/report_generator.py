"""Generate reports from learning recommendation data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, User, Recommendation, LearningObjective


class ReportGenerator:
    """Generate HTML and CSV reports from learning recommendation data."""

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
        self, user_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            user_id: Optional user ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(user_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(user_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, user_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            user_id: Optional user ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            if user_id:
                user = self.db_manager.get_user(user_id)
                users = [user] if user else []
            else:
                users = session.query(User).limit(10).all()

            if not users:
                return None

            user = users[0]

            from src.behavior_analyzer import BehaviorAnalyzer
            from src.completion_analyzer import CompletionAnalyzer
            from src.objective_tracker import ObjectiveTracker

            behavior_analyzer = BehaviorAnalyzer(
                self.db_manager, self.config.get("behavior_analysis", {})
            )
            completion_analyzer = CompletionAnalyzer(
                self.db_manager, self.config.get("completion_analysis", {})
            )
            objective_tracker = ObjectiveTracker(
                self.db_manager, self.config.get("objective_tracking", {})
            )

            behavior_analysis = behavior_analyzer.analyze_user_behavior(user.id)
            learning_style = behavior_analyzer.get_learning_style(user.id)
            completion_stats = completion_analyzer.get_user_completion_statistics(user.id)
            objectives_summary = objective_tracker.get_user_objectives_summary(user.id)
            recommendations = self.db_manager.get_user_recommendations(user.id, limit=10)

            template_path = Path(__file__).parent.parent / "templates" / "learning_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                username=user.username or user.user_id,
                behavior_analysis=behavior_analysis,
                learning_style=learning_style,
                completion_stats=completion_stats,
                objectives_summary=objectives_summary,
                recommendations=recommendations,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"learning_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, user_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            user_id: Optional user ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            if user_id:
                user = self.db_manager.get_user(user_id)
                users = [user] if user else []
            else:
                users = session.query(User).limit(10).all()

            if not users:
                return None

            user = users[0]
            recommendations = self.db_manager.get_user_recommendations(user.id)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"learning_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Course Name",
                    "Title",
                    "Confidence Score",
                    "Difficulty Level",
                    "Priority",
                    "Generated At",
                ])

                for rec in recommendations:
                    writer.writerow([
                        rec.course.course_name if rec.course else "Unknown",
                        rec.title,
                        rec.confidence_score,
                        rec.difficulty_level,
                        rec.priority,
                        rec.generated_at,
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
    <title>Learning Recommendation Report</title>
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
    <h1>Learning Recommendation Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Recommendations</h2>
    <table>
        <tr>
            <th>Course Name</th>
            <th>Confidence Score</th>
            <th>Difficulty</th>
            <th>Priority</th>
        </tr>
        {% for rec in recommendations %}
        <tr>
            <td>{{ rec.course.course_name if rec.course else 'Unknown' }}</td>
            <td>{{ "%.2f"|format(rec.confidence_score or 0) }}</td>
            <td>{{ rec.difficulty_level }}</td>
            <td>{{ rec.priority }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
