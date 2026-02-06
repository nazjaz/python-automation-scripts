"""Tracks study progress and completion."""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, StudySession, ProgressRecord, Course

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks study progress and completion rates."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize progress tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.progress_config = config.get("progress_tracking", {})
        self.completion_threshold = self.progress_config.get("completion_threshold", 0.8)

    def record_session_progress(
        self,
        session_id: int,
        hours_studied: float,
        completion_percentage: Optional[float] = None,
        topics_mastered: int = 0,
        topics_reviewed: int = 0,
    ) -> ProgressRecord:
        """Record progress for a study session.

        Args:
            session_id: Study session ID.
            hours_studied: Hours studied.
            completion_percentage: Optional completion percentage.
            topics_mastered: Number of topics mastered.
            topics_reviewed: Number of topics reviewed.

        Returns:
            ProgressRecord object.
        """
        session = (
            self.db_manager.get_session()
            .query(StudySession)
            .filter(StudySession.id == session_id)
            .first()
        )

        if not session:
            logger.error(f"Session {session_id} not found", extra={"session_id": session_id})
            raise ValueError(f"Session {session_id} not found")

        if completion_percentage is None:
            completion_percentage = min(hours_studied / (session.duration_minutes / 60.0), 1.0) if session.duration_minutes else 1.0

        progress = self.db_manager.add_progress_record(
            session_id=session_id,
            record_date=date.today(),
            hours_studied=hours_studied,
            completion_percentage=completion_percentage,
            topics_mastered=topics_mastered,
            topics_reviewed=topics_reviewed,
        )

        if completion_percentage >= self.completion_threshold:
            session.completion_status = "completed"
        elif completion_percentage >= 0.5:
            session.completion_status = "partial"
        else:
            session.completion_status = "incomplete"

        db_session = self.db_manager.get_session()
        try:
            db_session.merge(session)
            db_session.commit()
        finally:
            db_session.close()

        self._update_course_progress(session.course_id)

        logger.info(
            f"Recorded progress for session {session_id}",
            extra={
                "session_id": session_id,
                "completion_percentage": completion_percentage,
                "hours_studied": hours_studied,
            },
        )

        return progress

    def _update_course_progress(self, course_id: int) -> None:
        """Update course progress based on completed sessions.

        Args:
            course_id: Course ID.
        """
        sessions = self.db_manager.get_study_sessions(
            course_id=course_id, completion_status="completed"
        )

        total_hours = sum(
            s.duration_minutes / 60.0 if s.duration_minutes else 0.0
            for s in sessions
        )

        course = self.db_manager.get_session().query(Course).filter(Course.id == course_id).first()
        if course:
            course.hours_completed = total_hours
            db_session = self.db_manager.get_session()
            try:
                db_session.merge(course)
                db_session.commit()
            finally:
                db_session.close()

    def get_completion_rate(
        self,
        course_id: Optional[int] = None,
        days: int = 7,
    ) -> float:
        """Calculate completion rate for sessions.

        Args:
            course_id: Optional course ID filter.
            days: Number of days to analyze.

        Returns:
            Completion rate (0.0 to 1.0).
        """
        start_date = date.today() - timedelta(days=days)

        sessions = self.db_manager.get_study_sessions(
            course_id=course_id, start_date=start_date
        )

        if not sessions:
            return 0.0

        completed = len([s for s in sessions if s.completion_status == "completed"])
        return completed / float(len(sessions))

    def get_daily_progress(
        self,
        target_date: Optional[date] = None,
        course_id: Optional[int] = None,
    ) -> Dict:
        """Get progress for a specific day.

        Args:
            target_date: Target date (defaults to today).
            course_id: Optional course ID filter.

        Returns:
            Dictionary with daily progress metrics.
        """
        if target_date is None:
            target_date = date.today()

        sessions = self.db_manager.get_study_sessions(
            course_id=course_id,
            start_date=target_date,
            end_date=target_date,
        )

        total_hours = sum(
            s.duration_minutes / 60.0 if s.duration_minutes else 0.0
            for s in sessions
        )

        completed_sessions = len([s for s in sessions if s.completion_status == "completed"])
        scheduled_sessions = len(sessions)

        completion_rate = (
            completed_sessions / float(scheduled_sessions)
            if scheduled_sessions > 0
            else 0.0
        )

        return {
            "date": target_date.isoformat(),
            "scheduled_sessions": scheduled_sessions,
            "completed_sessions": completed_sessions,
            "completion_rate": completion_rate,
            "total_hours": total_hours,
        }

    def get_weekly_progress(
        self,
        course_id: Optional[int] = None,
    ) -> Dict:
        """Get progress for current week.

        Args:
            course_id: Optional course ID filter.

        Returns:
            Dictionary with weekly progress metrics.
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        sessions = self.db_manager.get_study_sessions(
            course_id=course_id,
            start_date=week_start,
            end_date=today,
        )

        total_hours = sum(
            s.duration_minutes / 60.0 if s.duration_minutes else 0.0
            for s in sessions
        )

        completed_sessions = len([s for s in sessions if s.completion_status == "completed"])
        scheduled_sessions = len(sessions)

        completion_rate = (
            completed_sessions / float(scheduled_sessions)
            if scheduled_sessions > 0
            else 0.0
        )

        daily_progress = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            if day <= today:
                daily_progress.append(self.get_daily_progress(target_date=day, course_id=course_id))

        return {
            "week_start": week_start.isoformat(),
            "week_end": today.isoformat(),
            "scheduled_sessions": scheduled_sessions,
            "completed_sessions": completed_sessions,
            "completion_rate": completion_rate,
            "total_hours": total_hours,
            "daily_progress": daily_progress,
        }

    def get_course_progress(
        self, course_id: int
    ) -> Dict:
        """Get overall progress for a course.

        Args:
            course_id: Course ID.

        Returns:
            Dictionary with course progress metrics.
        """
        course = (
            self.db_manager.get_session()
            .query(Course)
            .filter(Course.id == course_id)
            .first()
        )

        if not course:
            return {}

        sessions = self.db_manager.get_study_sessions(course_id=course_id)
        completed_sessions = len([s for s in sessions if s.completion_status == "completed"])

        progress_percentage = (
            course.hours_completed / course.total_hours_required
            if course.total_hours_required > 0
            else 0.0
        )

        exams = self.db_manager.get_exams(course_id=course_id, upcoming_only=True)

        return {
            "course_id": course_id,
            "course_name": course.name,
            "hours_completed": course.hours_completed,
            "total_hours_required": course.total_hours_required,
            "progress_percentage": progress_percentage,
            "total_sessions": len(sessions),
            "completed_sessions": completed_sessions,
            "upcoming_exams": len(exams),
        }
