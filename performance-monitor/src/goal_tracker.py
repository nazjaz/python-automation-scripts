"""Tracks employee goal completion."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Employee, Goal

logger = logging.getLogger(__name__)


class GoalTracker:
    """Tracks employee goal completion."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize goal tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.goals_config = config.get("goals", {})
        self.overdue_threshold = self.goals_config.get("overdue_threshold_days", 7)

    def update_goal_progress(
        self,
        goal_id: str,
        current_value: Optional[float] = None,
        completion_percentage: Optional[float] = None,
        status: Optional[str] = None,
    ) -> Goal:
        """Update goal progress.

        Args:
            goal_id: Goal ID.
            current_value: Optional current value.
            completion_percentage: Optional completion percentage.
            status: Optional status.

        Returns:
            Updated Goal object.
        """
        goal = (
            self.db_manager.get_session()
            .query(Goal)
            .filter(Goal.goal_id == goal_id)
            .first()
        )

        if not goal:
            raise ValueError(f"Goal {goal_id} not found")

        if current_value is not None:
            goal.current_value = current_value
            if goal.target_value and goal.target_value > 0:
                goal.completion_percentage = min((current_value / goal.target_value) * 100, 100.0)
            else:
                goal.completion_percentage = 0.0

        if completion_percentage is not None:
            goal.completion_percentage = min(completion_percentage, 100.0)

        if status:
            goal.status = status
        elif goal.completion_percentage >= 100.0:
            goal.status = "completed"
        elif goal.completion_percentage > 0:
            goal.status = "in_progress"

        goal.updated_at = datetime.utcnow()

        session = self.db_manager.get_session()
        try:
            session.merge(goal)
            session.commit()
            session.refresh(goal)
        finally:
            session.close()

        logger.info(
            f"Updated goal progress: {goal_id}",
            extra={
                "goal_id": goal_id,
                "completion_percentage": goal.completion_percentage,
                "status": goal.status,
            },
        )

        return goal

    def check_overdue_goals(
        self,
        employee_id: Optional[int] = None,
    ) -> List[Goal]:
        """Check for overdue goals.

        Args:
            employee_id: Optional employee ID filter.

        Returns:
            List of overdue Goal objects.
        """
        today = date.today()
        threshold_date = today - timedelta(days=self.overdue_threshold)

        query = (
            self.db_manager.get_session()
            .query(Goal)
            .filter(
                Goal.due_date < threshold_date,
                Goal.status.in_(["not_started", "in_progress"]),
            )
        )

        if employee_id:
            query = query.filter(Goal.employee_id == employee_id)

        overdue_goals = query.all()

        for goal in overdue_goals:
            if goal.status != "overdue":
                goal.status = "overdue"
                session = self.db_manager.get_session()
                try:
                    session.merge(goal)
                    session.commit()
                finally:
                    session.close()

        logger.info(
            f"Found {len(overdue_goals)} overdue goals",
            extra={"overdue_count": len(overdue_goals), "employee_id": employee_id},
        )

        return overdue_goals

    def get_goal_completion_summary(
        self,
        employee_id: int,
    ) -> Dict:
        """Get goal completion summary for employee.

        Args:
            employee_id: Employee ID.

        Returns:
            Dictionary with goal completion summary.
        """
        goals = self.db_manager.get_goals(employee_id=employee_id)

        summary = {
            "employee_id": employee_id,
            "total_goals": len(goals),
            "completed": len([g for g in goals if g.status == "completed"]),
            "in_progress": len([g for g in goals if g.status == "in_progress"]),
            "not_started": len([g for g in goals if g.status == "not_started"]),
            "overdue": len([g for g in goals if g.status == "overdue"]),
            "average_completion": 0.0,
        }

        if goals:
            summary["average_completion"] = float(
                sum(g.completion_percentage for g in goals) / len(goals)
            )

        logger.info(
            f"Goal completion summary for employee {employee_id}",
            extra=summary,
        )

        return summary
