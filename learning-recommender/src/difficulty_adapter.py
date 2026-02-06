"""Adapt difficulty levels based on user performance."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class DifficultyAdapter:
    """Adapt difficulty levels based on user performance."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize difficulty adapter.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.difficulty_levels = ["beginner", "intermediate", "advanced"]
        self.score_thresholds = config.get("score_thresholds", {
            "beginner": 0.7,
            "intermediate": 0.75,
            "advanced": 0.8,
        })

    def adapt_difficulty(self, user_id: int, course_id: int) -> Dict[str, any]:
        """Adapt difficulty level for user based on performance.

        Args:
            user_id: User ID.
            course_id: Course ID.

        Returns:
            Dictionary with adapted difficulty information.
        """
        user = self.db_manager.get_user(user_id)
        course = self.db_manager.get_course(course_id)

        if not user or not course:
            return {}

        enrollments = self.db_manager.get_user_enrollments(user_id)
        course_enrollment = next(
            (e for e in enrollments if e.course_id == course_id), None
        )

        if not course_enrollment:
            return {
                "recommended_difficulty": course.difficulty_level or "beginner",
                "confidence": 0.5,
                "reason": "No enrollment data available",
            }

        performance_score = self._calculate_performance_score(course_enrollment)
        current_difficulty = course.difficulty_level or "beginner"

        recommended_difficulty = self._recommend_difficulty(
            current_difficulty, performance_score
        )

        confidence = self._calculate_confidence(course_enrollment)

        return {
            "user_id": user_id,
            "course_id": course_id,
            "current_difficulty": current_difficulty,
            "recommended_difficulty": recommended_difficulty,
            "performance_score": performance_score,
            "confidence": confidence,
            "reason": self._get_recommendation_reason(
                current_difficulty, recommended_difficulty, performance_score
            ),
        }

    def _calculate_performance_score(self, enrollment) -> float:
        """Calculate user performance score.

        Args:
            enrollment: Enrollment object.

        Returns:
            Performance score (0.0 to 1.0).
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Progress

            progress_records = (
                session.query(Progress)
                .filter(Progress.enrollment_id == enrollment.id)
                .all()
            )

            if not progress_records:
                return 0.5

            scores = [p.score for p in progress_records if p.score is not None]
            if scores:
                avg_score = sum(scores) / len(scores)
                return avg_score / 100.0 if avg_score > 1.0 else avg_score

            completion_rates = [p.progress_percentage for p in progress_records]
            if completion_rates:
                return sum(completion_rates) / len(completion_rates)

            return enrollment.completion_rate or 0.5
        finally:
            session.close()

    def _recommend_difficulty(
        self, current_difficulty: str, performance_score: float
    ) -> str:
        """Recommend difficulty level.

        Args:
            current_difficulty: Current difficulty level.
            performance_score: Performance score (0.0 to 1.0).

        Returns:
            Recommended difficulty level.
        """
        current_index = self.difficulty_levels.index(
            current_difficulty
        ) if current_difficulty in self.difficulty_levels else 0

        threshold = self.score_thresholds.get(current_difficulty, 0.75)

        if performance_score >= threshold:
            if current_index < len(self.difficulty_levels) - 1:
                return self.difficulty_levels[current_index + 1]
        elif performance_score < threshold * 0.7:
            if current_index > 0:
                return self.difficulty_levels[current_index - 1]

        return current_difficulty

    def _calculate_confidence(self, enrollment) -> float:
        """Calculate confidence in difficulty recommendation.

        Args:
            enrollment: Enrollment object.

        Returns:
            Confidence score (0.0 to 1.0).
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Progress

            progress_records = (
                session.query(Progress)
                .filter(Progress.enrollment_id == enrollment.id)
                .all()
            )

            if len(progress_records) < 3:
                return 0.5

            return min(len(progress_records) / 10.0, 1.0)
        finally:
            session.close()

    def _get_recommendation_reason(
        self, current: str, recommended: str, performance_score: float
    ) -> str:
        """Get reason for difficulty recommendation.

        Args:
            current: Current difficulty level.
            recommended: Recommended difficulty level.
            performance_score: Performance score.

        Returns:
            Reason string.
        """
        if current == recommended:
            return f"Current difficulty ({current}) is appropriate for performance score {performance_score:.2f}"

        if recommended in ["intermediate", "advanced"] and current in ["beginner", "intermediate"]:
            return f"Performance score {performance_score:.2f} indicates readiness for {recommended} level"

        return f"Performance score {performance_score:.2f} suggests {recommended} level is more appropriate"

    def get_optimal_difficulty_for_objective(
        self, user_id: int, objective_id: int
    ) -> Dict[str, any]:
        """Get optimal difficulty for learning objective.

        Args:
            user_id: User ID.
            objective_id: Learning objective ID.

        Returns:
            Dictionary with optimal difficulty information.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import LearningObjective

            objective = (
                session.query(LearningObjective)
                .filter(LearningObjective.id == objective_id)
                .first()
            )

            if not objective:
                return {}

            user_stats = self._get_user_skill_level(user_id, objective.target_skill)

            if user_stats["skill_level"] == "beginner":
                recommended = "beginner"
            elif user_stats["skill_level"] == "intermediate":
                recommended = "intermediate"
            else:
                recommended = "advanced"

            return {
                "objective_id": objective_id,
                "target_skill": objective.target_skill,
                "user_skill_level": user_stats["skill_level"],
                "recommended_difficulty": recommended,
                "confidence": user_stats["confidence"],
            }
        finally:
            session.close()

    def _get_user_skill_level(
        self, user_id: int, skill: Optional[str]
    ) -> Dict[str, any]:
        """Get user skill level for a specific skill.

        Args:
            user_id: User ID.
            skill: Target skill.

        Returns:
            Dictionary with skill level information.
        """
        enrollments = self.db_manager.get_user_enrollments(user_id)

        if not enrollments:
            return {"skill_level": "beginner", "confidence": 0.3}

        completed_courses = [e for e in enrollments if e.status == "completed"]
        if not completed_courses:
            return {"skill_level": "beginner", "confidence": 0.5}

        avg_completion = (
            sum(e.completion_rate for e in completed_courses) / len(completed_courses)
        )

        if avg_completion >= 0.8:
            skill_level = "advanced"
        elif avg_completion >= 0.6:
            skill_level = "intermediate"
        else:
            skill_level = "beginner"

        confidence = min(len(completed_courses) / 5.0, 1.0)

        return {"skill_level": skill_level, "confidence": confidence}
