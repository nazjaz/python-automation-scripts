"""Generate reports from content recommendation data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, User, Recommendation, Content


class ReportGenerator:
    """Generate HTML and CSV reports from content recommendation data."""

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
            from src.preference_analyzer import PreferenceAnalyzer
            from src.history_analyzer import HistoryAnalyzer
            from src.engagement_analyzer import EngagementAnalyzer
            from src.recommendation_generator import RecommendationGenerator

            preference_analyzer = PreferenceAnalyzer(
                self.db_manager, self.config.get("preference_analysis", {})
            )
            history_analyzer = HistoryAnalyzer(
                self.db_manager, self.config.get("history_analysis", {})
            )
            engagement_analyzer = EngagementAnalyzer(
                self.db_manager, self.config.get("engagement_analysis", {})
            )
            recommendation_generator = RecommendationGenerator(
                self.db_manager, self.config.get("recommendation", {})
            )

            if user_id:
                user = self.db_manager.get_user(user_id)
                users = [user] if user else []
            else:
                users = session.query(User).limit(10).all()

            if not users:
                return None

            user_data = []
            for user in users:
                preferences = preference_analyzer.analyze_preferences(user.user_id)
                history = history_analyzer.analyze_history(user.user_id, days=30)
                engagement = engagement_analyzer.analyze_engagement(user.user_id, days=30)
                recommendations = recommendation_generator.get_recommendations(
                    user.user_id, limit=10
                )
                stats = recommendation_generator.get_recommendation_statistics(
                    user.user_id
                )

                user_data.append({
                    "user": user,
                    "preferences": preferences,
                    "history": history,
                    "engagement": engagement,
                    "recommendations": recommendations[:5],
                    "stats": stats,
                })

            template_path = Path(__file__).parent.parent / "templates" / "recommendation_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_data=user_data,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"recommendation_report_{timestamp}.html"

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
            from src.recommendation_generator import RecommendationGenerator

            generator = RecommendationGenerator(
                self.db_manager, self.config.get("recommendation", {})
            )

            if user_id:
                user = self.db_manager.get_user(user_id)
                users = [user] if user else []
            else:
                users = session.query(User).limit(50).all()

            if not users:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"recommendation_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "User ID",
                    "Content ID",
                    "Title",
                    "Content Type",
                    "Category",
                    "Score",
                    "Reason",
                    "Generated At",
                ])

                for user in users:
                    recommendations = generator.get_recommendations(user.user_id, limit=20)
                    for rec in recommendations:
                        writer.writerow([
                            user.user_id,
                            rec["content_id"],
                            rec["title"],
                            rec["content_type"],
                            rec["category"],
                            rec["score"],
                            rec["reason"],
                            rec["generated_at"],
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
    <title>Content Recommendation Report</title>
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
    <h1>Content Recommendation Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Users:</strong> {{ user_data|length }}
    </div>
    
    <h2>Recommendations</h2>
    <table>
        <tr>
            <th>User</th>
            <th>Content</th>
            <th>Score</th>
        </tr>
        {% for data in user_data %}
        {% for rec in data.recommendations %}
        <tr>
            <td>{{ data.user.username }}</td>
            <td>{{ rec.title }}</td>
            <td>{{ "%.2f"|format(rec.score) }}</td>
        </tr>
        {% endfor %}
        {% endfor %}
    </table>
</body>
</html>
"""
