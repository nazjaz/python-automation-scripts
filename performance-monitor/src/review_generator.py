"""Generates performance reviews."""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Employee, PerformanceReview
from src.performance_monitor import PerformanceMonitor
from src.goal_tracker import GoalTracker

logger = logging.getLogger(__name__)


class ReviewGenerator:
    """Generates performance reviews."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize review generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.reviews_config = config.get("reviews", {})
        self.performance_monitor = PerformanceMonitor(db_manager, config)
        self.goal_tracker = GoalTracker(db_manager, config)

    def generate_review(
        self,
        employee_id: int,
        review_type: str,
        review_period_start: Optional[date] = None,
        review_period_end: Optional[date] = None,
        output_path: Optional[str] = None,
    ) -> PerformanceReview:
        """Generate performance review for employee.

        Args:
            employee_id: Employee ID.
            review_type: Review type.
            review_period_start: Optional review period start date.
            review_period_end: Optional review period end date.
            output_path: Optional output file path.

        Returns:
            PerformanceReview object.
        """
        employee = (
            self.db_manager.get_session()
            .query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )

        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        if review_period_end is None:
            review_period_end = date.today()

        if review_period_start is None:
            if review_type == "quarterly":
                review_period_start = review_period_end - timedelta(days=90)
            elif review_type == "annual":
                review_period_start = review_period_end - timedelta(days=365)
            else:
                review_period_start = review_period_end - timedelta(days=90)

        performance_score = self.performance_monitor.calculate_performance_score(
            employee_id=employee_id,
            period_start=review_period_start,
            period_end=review_period_end,
        )

        goal_summary = self.goal_tracker.get_goal_completion_summary(employee_id=employee_id)

        from src.training_analyzer import TrainingAnalyzer
        training_analyzer = TrainingAnalyzer(self.db_manager, self.config)
        training_needs = training_analyzer.identify_training_needs(employee_id=employee_id)

        strengths = self._identify_strengths(performance_score, goal_summary)
        areas_for_improvement = self._identify_improvement_areas(performance_score, goal_summary, training_needs)
        recommendations = self._generate_recommendations(performance_score, goal_summary, training_needs)

        review_id = f"{employee.employee_id}_{review_type}_{review_period_end.strftime('%Y%m%d')}"

        if output_path is None:
            output_dir = Path(self.config.get("reporting", {}).get("output_directory", "reports"))
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"review_{review_id}.html")

        review_html = self._generate_review_html(
            employee=employee,
            review_type=review_type,
            review_period_start=review_period_start,
            review_period_end=review_period_end,
            performance_score=performance_score,
            goal_summary=goal_summary,
            training_needs=training_needs,
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            recommendations=recommendations,
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(review_html)

        review = self.db_manager.add_review(
            employee_id=employee_id,
            review_id=review_id,
            review_type=review_type,
            review_period_start=review_period_start,
            review_period_end=review_period_end,
            overall_rating=performance_score.get("overall_score"),
            overall_rating_category=performance_score.get("rating"),
            strengths="\n".join(strengths),
            areas_for_improvement="\n".join(areas_for_improvement),
            recommendations="\n".join(recommendations),
            file_path=output_path,
        )

        logger.info(
            f"Generated performance review for employee {employee_id}",
            extra={
                "employee_id": employee_id,
                "review_id": review_id,
                "overall_rating": performance_score.get("overall_score"),
            },
        )

        return review

    def _identify_strengths(
        self,
        performance_score: Dict,
        goal_summary: Dict,
    ) -> List[str]:
        """Identify employee strengths.

        Args:
            performance_score: Performance score dictionary.
            goal_summary: Goal summary dictionary.

        Returns:
            List of strength descriptions.
        """
        strengths = []

        if performance_score.get("overall_score", 0) >= 0.75:
            strengths.append("Consistently high performance across key metrics")

        metric_scores = performance_score.get("metric_scores", {})
        for metric_type, score in metric_scores.items():
            if score >= 0.80:
                strengths.append(f"Strong performance in {metric_type.replace('_', ' ')}")

        if goal_summary.get("completed", 0) > 0:
            completion_rate = goal_summary.get("completed", 0) / max(goal_summary.get("total_goals", 1), 1)
            if completion_rate >= 0.75:
                strengths.append("Excellent goal completion rate")

        return strengths if strengths else ["Consistent performance"]

    def _identify_improvement_areas(
        self,
        performance_score: Dict,
        goal_summary: Dict,
        training_needs: List,
    ) -> List[str]:
        """Identify areas for improvement.

        Args:
            performance_score: Performance score dictionary.
            goal_summary: Goal summary dictionary.
            training_needs: List of training needs.

        Returns:
            List of improvement area descriptions.
        """
        areas = []

        metric_scores = performance_score.get("metric_scores", {})
        for metric_type, score in metric_scores.items():
            if score < 0.60:
                areas.append(f"Improve performance in {metric_type.replace('_', ' ')}")

        if goal_summary.get("overdue", 0) > 0:
            areas.append("Address overdue goals and improve time management")

        if goal_summary.get("average_completion", 0) < 0.70:
            areas.append("Improve goal completion rate")

        if training_needs:
            high_priority = [tn for tn in training_needs if tn.priority == "high"]
            if high_priority:
                areas.append("Address high-priority training needs")

        return areas if areas else ["Continue current performance trajectory"]

    def _generate_recommendations(
        self,
        performance_score: Dict,
        goal_summary: Dict,
        training_needs: List,
    ) -> List[str]:
        """Generate recommendations.

        Args:
            performance_score: Performance score dictionary.
            goal_summary: Goal summary dictionary.
            training_needs: List of training needs.

        Returns:
            List of recommendations.
        """
        recommendations = []

        if performance_score.get("overall_score", 0) < 0.60:
            recommendations.append("Develop action plan to improve overall performance")

        if goal_summary.get("overdue", 0) > 0:
            recommendations.append("Review and prioritize goals to address overdue items")

        high_priority_training = [tn for tn in training_needs if tn.priority == "high"]
        if high_priority_training:
            recommendations.append("Prioritize high-priority training needs")

        if performance_score.get("overall_score", 0) >= 0.90:
            recommendations.append("Consider leadership opportunities or advanced projects")

        return recommendations if recommendations else ["Continue current development path"]

    def _generate_review_html(
        self,
        employee: Employee,
        review_type: str,
        review_period_start: date,
        review_period_end: date,
        performance_score: Dict,
        goal_summary: Dict,
        training_needs: List,
        strengths: List[str],
        areas_for_improvement: List[str],
        recommendations: List[str],
    ) -> str:
        """Generate review HTML.

        Args:
            employee: Employee object.
            review_type: Review type.
            review_period_start: Review period start date.
            review_period_end: Review period end date.
            performance_score: Performance score dictionary.
            goal_summary: Goal summary dictionary.
            training_needs: List of training needs.
            strengths: List of strengths.
            areas_for_improvement: List of improvement areas.
            recommendations: List of recommendations.

        Returns:
            HTML string.
        """
        template_path = Path(__file__).parent.parent / "templates" / "performance_review.html"
        if template_path.exists():
            with open(template_path, "r") as f:
                template_content = f.read()
        else:
            template_content = self._get_default_template()

        template = Template(template_content)

        return template.render(
            employee=employee,
            review_type=review_type,
            review_period_start=review_period_start,
            review_period_end=review_period_end,
            performance_score=performance_score,
            goal_summary=goal_summary,
            training_needs=training_needs,
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            recommendations=recommendations,
        )

    def _get_default_template(self) -> str:
        """Get default review template.

        Returns:
            Default HTML template string.
        """
        return """<!DOCTYPE html>
<html>
<head>
    <title>Performance Review</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .header { background: #667eea; color: white; padding: 20px; }
        .section { margin: 20px 0; }
        h2 { color: #667eea; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Performance Review</h1>
        <p>Employee: {{ employee.name }}</p>
        <p>Period: {{ review_period_start }} to {{ review_period_end }}</p>
    </div>
    <div class="section">
        <h2>Overall Rating</h2>
        <p>Score: {{ "%.2f"|format(performance_score.overall_score) }}</p>
        <p>Rating: {{ performance_score.rating|title }}</p>
    </div>
    <div class="section">
        <h2>Strengths</h2>
        <ul>
            {% for strength in strengths %}
            <li>{{ strength }}</li>
            {% endfor %}
        </ul>
    </div>
    <div class="section">
        <h2>Areas for Improvement</h2>
        <ul>
            {% for area in areas_for_improvement %}
            <li>{{ area }}</li>
            {% endfor %}
        </ul>
    </div>
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            {% for rec in recommendations %}
            <li>{{ rec }}</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>"""
