"""Generates adjustment recommendations based on progress and performance."""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Recommendation, Course, Exam, StudySession

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates recommendations for schedule adjustments and improvements."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize recommendation engine.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.recommendation_config = config.get("recommendations", {})
        self.progress_config = config.get("progress_tracking", {})
        self.adjustment_threshold = self.progress_config.get("adjustment_threshold", 0.6)

    def generate_recommendations(
        self,
        course_id: Optional[int] = None,
        days: int = 7,
    ) -> List[Recommendation]:
        """Generate recommendations based on progress analysis.

        Args:
            course_id: Optional course ID filter.
            days: Number of days to analyze.

        Returns:
            List of Recommendation objects.
        """
        from src.progress_tracker import ProgressTracker

        tracker = ProgressTracker(self.db_manager, self.config)

        recommendations = []

        completion_rate = tracker.get_completion_rate(course_id=course_id, days=days)

        if completion_rate < self.adjustment_threshold:
            recommendations.append(
                self._create_schedule_adjustment_recommendation(
                    completion_rate, course_id
                )
            )

        recommendations.extend(self._check_exam_preparation(course_id))
        recommendations.extend(self._check_study_load_balance(course_id))
        recommendations.extend(self._check_learning_methods(course_id))

        for rec in recommendations:
            self.db_manager.add_recommendation(
                recommendation_type=rec["type"],
                title=rec["title"],
                description=rec["description"],
                priority=rec["priority"],
                course_id=rec.get("course_id"),
            )

        logger.info(
            f"Generated {len(recommendations)} recommendations",
            extra={"recommendation_count": len(recommendations), "course_id": course_id},
        )

        return recommendations

    def _create_schedule_adjustment_recommendation(
        self,
        completion_rate: float,
        course_id: Optional[int],
    ) -> Dict:
        """Create schedule adjustment recommendation.

        Args:
            completion_rate: Current completion rate.
            course_id: Optional course ID.

        Returns:
            Recommendation dictionary.
        """
        if completion_rate < 0.3:
            priority = "high"
            suggestion = "Consider reducing daily study hours or breaking sessions into smaller chunks"
        elif completion_rate < 0.5:
            priority = "medium"
            suggestion = "Try adjusting study times to better match your availability"
        else:
            priority = "low"
            suggestion = "Minor schedule adjustments may help improve completion rates"

        return {
            "type": "schedule_adjustment",
            "title": "Schedule Adjustment Needed",
            "description": f"Current completion rate is {completion_rate:.1%}. {suggestion}.",
            "priority": priority,
            "course_id": course_id,
        }

    def _check_exam_preparation(
        self, course_id: Optional[int]
    ) -> List[Dict]:
        """Check exam preparation status and generate recommendations.

        Args:
            course_id: Optional course ID filter.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        exams = self.db_manager.get_exams(upcoming_only=True)
        if course_id:
            exams = [e for e in exams if e.course_id == course_id]

        today = date.today()

        for exam in exams:
            days_until_exam = (exam.exam_date - today).days

            if days_until_exam <= 7:
                course = self.db_manager.get_session().query(Course).filter(Course.id == exam.course_id).first()
                sessions = self.db_manager.get_study_sessions(
                    course_id=exam.course_id,
                    start_date=today,
                    end_date=exam.exam_date,
                )

                if len(sessions) < 5:
                    recommendations.append(
                        {
                            "type": "exam_preparation",
                            "title": f"Intensive Preparation Needed for {exam.name}",
                            "description": f"Only {days_until_exam} days until {exam.name}. "
                            f"Consider increasing study sessions for {course.name if course else 'this course'}.",
                            "priority": "high",
                            "course_id": exam.course_id,
                        }
                    )

        return recommendations

    def _check_study_load_balance(
        self, course_id: Optional[int]
    ) -> List[Dict]:
        """Check study load balance across courses.

        Args:
            course_id: Optional course ID filter.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        courses = self.db_manager.get_courses()
        if course_id:
            courses = [c for c in courses if c.id == course_id]

        if len(courses) < 2:
            return recommendations

        course_loads = []

        for course in courses:
            sessions = self.db_manager.get_study_sessions(course_id=course.id)
            total_hours = sum(
                s.duration_minutes / 60.0 if s.duration_minutes else 0.0
                for s in sessions
            )
            course_loads.append((total_hours, course))

        if not course_loads:
            return recommendations

        avg_load = sum(load for load, _ in course_loads) / len(course_loads)
        max_load = max(load for load, _ in course_loads)
        min_load = min(load for load, _ in course_loads)

        if max_load > avg_load * 1.5:
            overloaded_course = next(c for load, c in course_loads if load == max_load)
            recommendations.append(
                {
                    "type": "load_balance",
                    "title": "Study Load Imbalance Detected",
                    "description": f"{overloaded_course.name} has significantly more study hours than average. "
                    f"Consider redistributing study time across courses.",
                    "priority": "medium",
                    "course_id": overloaded_course.id,
                }
            )

        if min_load < avg_load * 0.5 and min_load > 0:
            underloaded_course = next(c for load, c in course_loads if load == min_load)
            recommendations.append(
                {
                    "type": "load_balance",
                    "title": "Understudied Course Detected",
                    "description": f"{underloaded_course.name} has fewer study hours than average. "
                    f"Consider increasing focus on this course.",
                    "priority": "low",
                    "course_id": underloaded_course.id,
                }
            )

        return recommendations

    def _check_learning_methods(
        self, course_id: Optional[int]
    ) -> List[Dict]:
        """Check learning methods and suggest improvements.

        Args:
            course_id: Optional course ID filter.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        preference = self.db_manager.get_learning_preference()

        if not preference:
            return recommendations

        if not preference.active_recall_enabled:
            recommendations.append(
                {
                    "type": "learning_method",
                    "title": "Enable Active Recall",
                    "description": "Active recall techniques can improve retention. "
                    "Consider incorporating practice tests and self-quizzing into your study routine.",
                    "priority": "medium",
                    "course_id": course_id,
                }
            )

        if not preference.spaced_repetition_enabled:
            recommendations.append(
                {
                    "type": "learning_method",
                    "title": "Use Spaced Repetition",
                    "description": "Spaced repetition helps with long-term retention. "
                    "Consider scheduling regular review sessions for previously covered material.",
                    "priority": "medium",
                    "course_id": course_id,
                }
            )

        sessions = self.db_manager.get_study_sessions(course_id=course_id)
        low_effectiveness = [
            s for s in sessions
            if s.effectiveness_rating is not None and s.effectiveness_rating <= 2
        ]

        if len(low_effectiveness) >= 3:
            recommendations.append(
                {
                    "type": "learning_method",
                    "title": "Review Study Methods",
                    "description": f"Several study sessions have low effectiveness ratings. "
                    f"Consider trying different study techniques or adjusting your learning approach.",
                    "priority": "low",
                    "course_id": course_id,
                }
            )

        return recommendations
