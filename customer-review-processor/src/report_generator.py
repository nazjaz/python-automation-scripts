"""Generate reports from review analysis."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Review


class ReportGenerator:
    """Generate HTML and CSV reports from review analysis."""

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
        self, product_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            product_id: Optional product ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(product_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(product_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(self, product_id: Optional[str] = None) -> Optional[Path]:
        """Generate HTML report.

        Args:
            product_id: Optional product ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            reviews = session.query(self.db_manager.Review).all()
            if product_id:
                reviews = [r for r in reviews if r.product_id == product_id]

            if not reviews:
                return None

            issues = self.db_manager.get_all_issues()
            recommendations = self.db_manager.get_all_recommendations()

            sentiment_stats = self._calculate_sentiment_statistics(reviews)
            theme_stats = self._calculate_theme_statistics(reviews)
            issue_stats = self._calculate_issue_statistics(issues)

            template_path = Path(__file__).parent.parent / "templates" / "review_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_reviews=len(reviews),
                sentiment_stats=sentiment_stats,
                theme_stats=theme_stats,
                issue_stats=issue_stats,
                top_issues=issues[:10],
                top_recommendations=recommendations[:10],
                reviews=reviews[:50],
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"review_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(self, product_id: Optional[str] = None) -> Optional[Path]:
        """Generate CSV report.

        Args:
            product_id: Optional product ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            reviews = session.query(Review).all()
            if product_id:
                reviews = [r for r in reviews if r.product_id == product_id]

            if not reviews:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"review_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Review ID",
                    "Product ID",
                    "Product Name",
                    "Rating",
                    "Sentiment Score",
                    "Sentiment Label",
                    "Review Text",
                    "Source",
                    "Created At",
                ])

                for review in reviews:
                    writer.writerow([
                        review.id,
                        review.product_id,
                        review.product_name,
                        review.rating,
                        review.sentiment_score,
                        review.sentiment_label,
                        review.review_text[:200] + "..." if len(review.review_text) > 200 else review.review_text,
                        review.source,
                        review.created_at,
                    ])

            return output_path
        finally:
            session.close()

    def _calculate_sentiment_statistics(self, reviews: List) -> Dict[str, any]:
        """Calculate sentiment statistics.

        Args:
            reviews: List of review objects.

        Returns:
            Sentiment statistics dictionary.
        """
        if not reviews:
            return {
                "average_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            }

        scores = [r.sentiment_score for r in reviews if r.sentiment_score is not None]
        labels = [r.sentiment_label for r in reviews if r.sentiment_label]

        return {
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "positive_count": labels.count("positive"),
            "negative_count": labels.count("negative"),
            "neutral_count": labels.count("neutral"),
        }

    def _calculate_theme_statistics(self, reviews: List) -> Dict[str, any]:
        """Calculate theme statistics.

        Args:
            reviews: List of review objects.

        Returns:
            Theme statistics dictionary.
        """
        all_themes = []
        for review in reviews:
            all_themes.extend(review.themes)

        if not all_themes:
            return {"total_themes": 0, "by_category": {}}

        categories = [theme.category for theme in all_themes if theme.category]
        from collections import Counter
        category_counts = Counter(categories)

        return {
            "total_themes": len(all_themes),
            "by_category": dict(category_counts),
        }

    def _calculate_issue_statistics(self, issues: List) -> Dict[str, any]:
        """Calculate issue statistics.

        Args:
            issues: List of issue objects.

        Returns:
            Issue statistics dictionary.
        """
        if not issues:
            return {
                "total_issues": 0,
                "by_severity": {},
                "by_category": {},
            }

        severities = [issue.severity for issue in issues if issue.severity]
        categories = [issue.category for issue in issues if issue.category]

        from collections import Counter
        severity_counts = Counter(severities)
        category_counts = Counter(categories)

        return {
            "total_issues": len(issues),
            "by_severity": dict(severity_counts),
            "by_category": dict(category_counts),
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
    <title>Customer Review Analysis Report</title>
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
    <h1>Customer Review Analysis Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Reviews:</strong> {{ total_reviews }}
    </div>
    
    <h2>Sentiment Statistics</h2>
    <div class="stat-box">
        <strong>Average Score:</strong> {{ "%.2f"|format(sentiment_stats.average_score) }}
    </div>
    <div class="stat-box">
        <strong>Positive:</strong> {{ sentiment_stats.positive_count }}
    </div>
    <div class="stat-box">
        <strong>Negative:</strong> {{ sentiment_stats.negative_count }}
    </div>
    <div class="stat-box">
        <strong>Neutral:</strong> {{ sentiment_stats.neutral_count }}
    </div>
    
    <h2>Top Recommendations</h2>
    <table>
        <tr>
            <th>Priority</th>
            <th>Category</th>
            <th>Recommendation</th>
            <th>Impact Score</th>
        </tr>
        {% for rec in top_recommendations %}
        <tr>
            <td>{{ rec.priority }}</td>
            <td>{{ rec.category }}</td>
            <td>{{ rec.recommendation_text }}</td>
            <td>{{ "%.2f"|format(rec.impact_score) }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
