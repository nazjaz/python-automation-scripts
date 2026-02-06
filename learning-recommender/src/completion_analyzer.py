"""Analyze course completion rates."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class CompletionAnalyzer:
    """Analyze course completion rates."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize completion analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def analyze_completion_rate(
        self, course_id: int, days: Optional[int] = None
    ) -> Dict[str, any]:
        """Analyze completion rate for a course.

        Args:
            course_id: Course ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with completion rate analysis.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Enrollment

            query = session.query(Enrollment).filter(Enrollment.course_id == course_id)

            if days:
                cutoff = datetime.utcnow() - timedelta(days=days)
                query = query.filter(Enrollment.enrolled_at >= cutoff)

            enrollments = query.all()

            total_enrollments = len(enrollments)
            completed_enrollments = len([e for e in enrollments if e.status == "completed"])

            completion_rate = (
                completed_enrollments / total_enrollments * 100
                if total_enrollments > 0
                else 0.0
            )

            completion_times = []
            for enrollment in enrollments:
                if enrollment.completed_at and enrollment.enrolled_at:
                    duration = (enrollment.completed_at - enrollment.enrolled_at).total_seconds() / 60
                    completion_times.append(duration)

            average_completion_time = (
                sum(completion_times) / len(completion_times)
                if completion_times
                else None
            )

            time_window_start = cutoff if days else datetime.utcnow() - timedelta(days=30)
            time_window_end = datetime.utcnow()

            self.db_manager.add_completion_rate(
                course_id=course_id,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_enrollments=total_enrollments,
                completed_enrollments=completed_enrollments,
                average_completion_time=average_completion_time,
            )

            return {
                "course_id": course_id,
                "total_enrollments": total_enrollments,
                "completed_enrollments": completed_enrollments,
                "completion_rate": completion_rate,
                "average_completion_time": average_completion_time,
            }
        finally:
            session.close()

    def get_user_completion_statistics(self, user_id: int) -> Dict[str, any]:
        """Get user completion statistics.

        Args:
            user_id: User ID.

        Returns:
            Dictionary with user completion statistics.
        """
        enrollments = self.db_manager.get_user_enrollments(user_id)

        if not enrollments:
            return {
                "user_id": user_id,
                "total_enrollments": 0,
                "completed_enrollments": 0,
                "average_completion_rate": 0.0,
            }

        total_enrollments = len(enrollments)
        completed_enrollments = len([e for e in enrollments if e.status == "completed"])

        completion_rates = [e.completion_rate for e in enrollments if e.completion_rate is not None]
        average_completion_rate = (
            sum(completion_rates) / len(completion_rates)
            if completion_rates
            else 0.0
        )

        return {
            "user_id": user_id,
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "average_completion_rate": average_completion_rate,
            "completion_rate_percentage": (
                completed_enrollments / total_enrollments * 100
                if total_enrollments > 0
                else 0.0
            ),
        }

    def get_course_completion_trends(
        self, course_id: int, days: int = 30
    ) -> Dict[str, any]:
        """Get completion rate trends for a course.

        Args:
            course_id: Course ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with completion trends.
        """
        completion_rates = self.db_manager.get_completion_rates(course_id=course_id)

        if not completion_rates:
            return {
                "course_id": course_id,
                "days": days,
                "average_rate": 0.0,
                "trend": "stable",
            }

        rates = [
            cr.completion_rate
            for cr in completion_rates
            if cr.completion_rate is not None
        ]

        if not rates:
            return {
                "course_id": course_id,
                "days": days,
                "average_rate": 0.0,
                "trend": "stable",
            }

        average_rate = sum(rates) / len(rates)

        trend = self._calculate_trend(rates)

        return {
            "course_id": course_id,
            "days": days,
            "average_rate": average_rate,
            "min_rate": min(rates),
            "max_rate": max(rates),
            "trend": trend,
        }

    def _calculate_trend(self, rates: List[float]) -> str:
        """Calculate trend from rates.

        Args:
            rates: List of completion rates.

        Returns:
            Trend indicator (increasing, decreasing, stable).
        """
        if len(rates) < 2:
            return "stable"

        mid_point = len(rates) // 2
        first_half_avg = sum(rates[:mid_point]) / len(rates[:mid_point])
        second_half_avg = sum(rates[mid_point:]) / len(rates[mid_point:])

        if second_half_avg > first_half_avg * 1.05:
            return "increasing"
        elif second_half_avg < first_half_avg * 0.95:
            return "decreasing"
        else:
            return "stable"
