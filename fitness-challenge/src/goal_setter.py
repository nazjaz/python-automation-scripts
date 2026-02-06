"""Set and manage fitness goals for participants."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class GoalSetter:
    """Set and manage fitness goals."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize goal setter.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.goal_templates = config.get("goal_templates", {})
        self.default_duration_days = config.get("default_duration_days", 30)

    def set_goal(
        self,
        participant_id: int,
        goal_type: str,
        target_value: float,
        unit: Optional[str] = None,
        deadline: Optional[datetime] = None,
    ) -> Dict[str, any]:
        """Set a fitness goal for participant.

        Args:
            participant_id: Participant ID.
            goal_type: Goal type (weight_loss, muscle_gain, steps, distance, etc.).
            target_value: Target value.
            unit: Unit of measurement.
            deadline: Goal deadline.

        Returns:
            Dictionary with goal information.
        """
        template = self.goal_templates.get(goal_type, {})
        goal_name = template.get("name", f"{goal_type.replace('_', ' ').title()} Goal")

        if unit is None:
            unit = template.get("default_unit", "")

        if deadline is None:
            deadline = datetime.utcnow() + timedelta(days=self.default_duration_days)

        goal = self.db_manager.create_goal(
            participant_id=participant_id,
            goal_name=goal_name,
            goal_type=goal_type,
            target_value=target_value,
            unit=unit,
            deadline=deadline,
        )

        return {
            "id": goal.id,
            "goal_name": goal.goal_name,
            "goal_type": goal.goal_type,
            "target_value": goal.target_value,
            "current_value": goal.current_value,
            "unit": goal.unit,
            "deadline": goal.deadline,
            "status": goal.status,
        }

    def set_personalized_goals(
        self, participant_id: int, fitness_level: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """Set personalized goals based on participant profile.

        Args:
            participant_id: Participant ID.
            fitness_level: Fitness level (beginner, intermediate, advanced).

        Returns:
            List of goal dictionaries.
        """
        participant = self.db_manager.get_participant(participant_id)
        if not participant:
            return []

        if fitness_level is None:
            fitness_level = participant.fitness_level or "beginner"

        goals = []
        level_config = self.config.get("fitness_levels", {}).get(fitness_level, {})

        default_goals = level_config.get("default_goals", [])

        for goal_config in default_goals:
            goal_type = goal_config.get("type")
            target_value = goal_config.get("target_value", 0)
            unit = goal_config.get("unit", "")
            duration_days = goal_config.get("duration_days", self.default_duration_days)

            deadline = datetime.utcnow() + timedelta(days=duration_days)

            goal = self.set_goal(
                participant_id=participant_id,
                goal_type=goal_type,
                target_value=target_value,
                unit=unit,
                deadline=deadline,
            )
            goals.append(goal)

        return goals

    def update_goal_progress(
        self, goal_id: int, progress_value: float
    ) -> Dict[str, any]:
        """Update goal progress.

        Args:
            goal_id: Goal ID.
            progress_value: Progress value to add.

        Returns:
            Updated goal dictionary.
        """
        goal = self.db_manager.get_session().query(
            self.db_manager.Goal
        ).filter(self.db_manager.Goal.id == goal_id).first()

        if not goal:
            return {}

        self.db_manager.add_progress_entry(
            participant_id=goal.participant_id,
            value=progress_value,
            unit=goal.unit,
            goal_id=goal_id,
        )

        updated_goal = self.db_manager.get_session().query(
            self.db_manager.Goal
        ).filter(self.db_manager.Goal.id == goal_id).first()

        return {
            "id": updated_goal.id,
            "goal_name": updated_goal.goal_name,
            "target_value": updated_goal.target_value,
            "current_value": updated_goal.current_value,
            "progress_percentage": (
                updated_goal.current_value / updated_goal.target_value * 100
                if updated_goal.target_value > 0
                else 0
            ),
            "status": updated_goal.status,
        }

    def get_goal_progress(self, goal_id: int) -> Dict[str, any]:
        """Get goal progress information.

        Args:
            goal_id: Goal ID.

        Returns:
            Goal progress dictionary.
        """
        from src.database import Goal

        session = self.db_manager.get_session()
        try:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if not goal:
                return {}

            progress_entries = self.db_manager.get_progress_entries(goal_id=goal_id)

            return {
                "id": goal.id,
                "goal_name": goal.goal_name,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "unit": goal.unit,
                "progress_percentage": (
                    goal.current_value / goal.target_value * 100
                    if goal.target_value > 0
                    else 0
                ),
                "deadline": goal.deadline,
                "status": goal.status,
                "entries_count": len(progress_entries),
            }
        finally:
            session.close()

    def get_participant_goals(
        self, participant_id: int, status: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """Get all goals for participant.

        Args:
            participant_id: Participant ID.
            status: Optional status filter (active, completed, cancelled).

        Returns:
            List of goal dictionaries.
        """
        goals = self.db_manager.get_active_goals(participant_id=participant_id)

        if status:
            goals = [g for g in goals if g.status == status]

        return [
            {
                "id": goal.id,
                "goal_name": goal.goal_name,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "unit": goal.unit,
                "progress_percentage": (
                    goal.current_value / goal.target_value * 100
                    if goal.target_value > 0
                    else 0
                ),
                "deadline": goal.deadline,
                "status": goal.status,
            }
            for goal in goals
        ]
