"""Track fitness progress for challenges and goals."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ProgressTracker:
    """Track fitness progress."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize progress tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def record_progress(
        self,
        participant_id: int,
        value: float,
        unit: str,
        challenge_id: Optional[int] = None,
        goal_id: Optional[int] = None,
        entry_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, any]:
        """Record progress entry.

        Args:
            participant_id: Participant ID.
            value: Progress value.
            unit: Unit of measurement.
            challenge_id: Optional challenge ID.
            goal_id: Optional goal ID.
            entry_date: Entry date.
            notes: Optional notes.

        Returns:
            Dictionary with progress entry information.
        """
        progress_entry = self.db_manager.add_progress_entry(
            participant_id=participant_id,
            value=value,
            unit=unit,
            challenge_id=challenge_id,
            goal_id=goal_id,
            entry_date=entry_date,
            notes=notes,
        )

        return {
            "id": progress_entry.id,
            "participant_id": progress_entry.participant_id,
            "challenge_id": progress_entry.challenge_id,
            "goal_id": progress_entry.goal_id,
            "value": progress_entry.value,
            "unit": progress_entry.unit,
            "entry_date": progress_entry.entry_date,
            "notes": progress_entry.notes,
        }

    def get_progress_summary(
        self,
        participant_id: int,
        days: int = 7,
        challenge_id: Optional[int] = None,
        goal_id: Optional[int] = None,
    ) -> Dict[str, any]:
        """Get progress summary.

        Args:
            participant_id: Participant ID.
            days: Number of days to summarize.
            challenge_id: Optional challenge ID to filter by.
            goal_id: Optional goal ID to filter by.

        Returns:
            Dictionary with progress summary.
        """
        progress_entries = self.db_manager.get_progress_entries(
            participant_id=participant_id,
            challenge_id=challenge_id,
            goal_id=goal_id,
            days=days,
        )

        if not progress_entries:
            return {
                "total_value": 0.0,
                "entry_count": 0,
                "average_daily": 0.0,
                "days": days,
            }

        total_value = sum(pe.value for pe in progress_entries)
        entry_count = len(progress_entries)
        average_daily = total_value / days if days > 0 else 0.0

        unit = progress_entries[0].unit if progress_entries else ""

        return {
            "total_value": total_value,
            "entry_count": entry_count,
            "average_daily": average_daily,
            "unit": unit,
            "days": days,
            "first_entry": progress_entries[-1].entry_date if progress_entries else None,
            "last_entry": progress_entries[0].entry_date if progress_entries else None,
        }

    def get_challenge_progress(
        self, challenge_id: int
    ) -> Dict[str, any]:
        """Get challenge progress.

        Args:
            challenge_id: Challenge ID.

        Returns:
            Dictionary with challenge progress.
        """
        from src.database import Challenge

        session = self.db_manager.get_session()
        try:
            challenge = session.query(Challenge).filter(Challenge.id == challenge_id).first()
            if not challenge:
                return {}

            progress_entries = self.db_manager.get_progress_entries(challenge_id=challenge_id)
            total_progress = sum(pe.value for pe in progress_entries)

            days_elapsed = (datetime.utcnow() - challenge.start_date).days + 1
            days_total = (challenge.end_date - challenge.start_date).days + 1

            expected_progress = (
                challenge.target_value * days_elapsed / days_total
                if days_total > 0
                else 0
            )

            progress_percentage = (
                total_progress / challenge.target_value * 100
                if challenge.target_value and challenge.target_value > 0
                else 0
            )

            return {
                "challenge_id": challenge.id,
                "challenge_name": challenge.challenge_name,
                "target_value": challenge.target_value,
                "current_value": total_progress,
                "expected_value": expected_progress,
                "progress_percentage": progress_percentage,
                "on_track": total_progress >= expected_progress * 0.9,
                "days_elapsed": days_elapsed,
                "days_total": days_total,
                "entries_count": len(progress_entries),
            }
        finally:
            session.close()

    def get_goal_progress(self, goal_id: int) -> Dict[str, any]:
        """Get goal progress.

        Args:
            goal_id: Goal ID.

        Returns:
            Dictionary with goal progress.
        """
        from src.database import Goal

        session = self.db_manager.get_session()
        try:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if not goal:
                return {}

            progress_entries = self.db_manager.get_progress_entries(goal_id=goal_id)
            total_progress = sum(pe.value for pe in progress_entries)

            progress_percentage = (
                total_progress / goal.target_value * 100
                if goal.target_value and goal.target_value > 0
                else 0
            )

            days_remaining = None
            if goal.deadline:
                days_remaining = (goal.deadline - datetime.utcnow()).days

            return {
                "goal_id": goal.id,
                "goal_name": goal.goal_name,
                "target_value": goal.target_value,
                "current_value": total_progress,
                "progress_percentage": progress_percentage,
                "days_remaining": days_remaining,
                "status": goal.status,
                "entries_count": len(progress_entries),
            }
        finally:
            session.close()

    def get_participant_statistics(
        self, participant_id: int, days: int = 30
    ) -> Dict[str, any]:
        """Get participant statistics.

        Args:
            participant_id: Participant ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with participant statistics.
        """
        progress_entries = self.db_manager.get_progress_entries(
            participant_id=participant_id, days=days
        )

        active_challenges = self.db_manager.get_active_challenges(
            participant_id=participant_id
        )
        active_goals = self.db_manager.get_active_goals(participant_id=participant_id)

        total_progress = sum(pe.value for pe in progress_entries)
        entry_count = len(progress_entries)

        completed_goals = len([g for g in active_goals if g.status == "completed"])

        return {
            "participant_id": participant_id,
            "total_progress": total_progress,
            "entry_count": entry_count,
            "active_challenges": len(active_challenges),
            "active_goals": len(active_goals),
            "completed_goals": completed_goals,
            "days_analyzed": days,
            "average_daily": total_progress / days if days > 0 else 0.0,
        }
