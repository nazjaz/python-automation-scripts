"""Track learning objectives and progress."""

from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ObjectiveTracker:
    """Track learning objectives and progress."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize objective tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def track_objective_progress(self, objective_id: int) -> Dict[str, any]:
        """Track progress toward learning objective.

        Args:
            objective_id: Learning objective ID.

        Returns:
            Dictionary with objective progress information.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import LearningObjective, Enrollment, Course

            objective = (
                session.query(LearningObjective)
                .filter(LearningObjective.id == objective_id)
                .first()
            )

            if not objective:
                return {}

            user_enrollments = self.db_manager.get_user_enrollments(objective.user_id)

            relevant_enrollments = []
            for enrollment in user_enrollments:
                if enrollment.course:
                    if objective.target_skill:
                        if objective.target_skill.lower() in (
                            enrollment.course.category or ""
                        ).lower():
                            relevant_enrollments.append(enrollment)
                    else:
                        relevant_enrollments.append(enrollment)

            total_progress = (
                sum(e.completion_rate for e in relevant_enrollments)
                / len(relevant_enrollments)
                if relevant_enrollments
                else 0.0
            )

            completed_count = len([e for e in relevant_enrollments if e.status == "completed"])

            days_remaining = None
            if objective.target_date:
                days_remaining = (objective.target_date - datetime.utcnow()).days

            return {
                "objective_id": objective_id,
                "objective_name": objective.objective_name,
                "target_skill": objective.target_skill,
                "total_progress": total_progress,
                "relevant_courses": len(relevant_enrollments),
                "completed_courses": completed_count,
                "days_remaining": days_remaining,
                "status": objective.status,
            }
        finally:
            session.close()

    def get_user_objectives_summary(self, user_id: int) -> Dict[str, any]:
        """Get summary of user learning objectives.

        Args:
            user_id: User ID.

        Returns:
            Dictionary with objectives summary.
        """
        objectives = self.db_manager.get_user_objectives(user_id, status="active")

        if not objectives:
            return {
                "user_id": user_id,
                "total_objectives": 0,
                "active_objectives": 0,
                "average_progress": 0.0,
            }

        progress_data = []
        for objective in objectives:
            progress = self.track_objective_progress(objective.id)
            if progress:
                progress_data.append(progress.get("total_progress", 0.0))

        average_progress = (
            sum(progress_data) / len(progress_data) if progress_data else 0.0
        )

        return {
            "user_id": user_id,
            "total_objectives": len(objectives),
            "active_objectives": len([o for o in objectives if o.status == "active"]),
            "average_progress": average_progress,
            "objectives": [
                {
                    "id": o.id,
                    "name": o.objective_name,
                    "target_skill": o.target_skill,
                    "priority": o.priority,
                }
                for o in objectives
            ],
        }

    def get_recommended_courses_for_objective(
        self, objective_id: int, limit: int = 5
    ) -> List[Dict[str, any]]:
        """Get recommended courses for learning objective.

        Args:
            objective_id: Learning objective ID.
            limit: Maximum number of courses to return.

        Returns:
            List of recommended course dictionaries.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import LearningObjective, Course

            objective = (
                session.query(LearningObjective)
                .filter(LearningObjective.id == objective_id)
                .first()
            )

            if not objective:
                return []

            query = session.query(Course)

            if objective.target_skill:
                query = query.filter(Course.category.ilike(f"%{objective.target_skill}%"))

            courses = query.limit(limit).all()

            return [
                {
                    "course_id": c.course_id,
                    "course_name": c.course_name,
                    "category": c.category,
                    "difficulty_level": c.difficulty_level,
                }
                for c in courses
            ]
        finally:
            session.close()
