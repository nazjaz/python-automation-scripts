"""Identifies training needs and creates development plans."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Employee, TrainingNeed, DevelopmentPlan
from src.performance_monitor import PerformanceMonitor
from src.goal_tracker import GoalTracker

logger = logging.getLogger(__name__)


class TrainingAnalyzer:
    """Identifies training needs and creates development plans."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize training analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.training_config = config.get("training", {})
        self.development_config = config.get("development_plans", {})
        self.performance_monitor = PerformanceMonitor(db_manager, config)
        self.goal_tracker = GoalTracker(db_manager, config)

    def identify_training_needs(
        self,
        employee_id: int,
    ) -> List[TrainingNeed]:
        """Identify training needs for employee.

        Args:
            employee_id: Employee ID.

        Returns:
            List of TrainingNeed objects.
        """
        performance_score = self.performance_monitor.calculate_performance_score(employee_id=employee_id)
        goal_summary = self.goal_tracker.get_goal_completion_summary(employee_id=employee_id)

        training_needs = []

        metric_scores = performance_score.get("metric_scores", {})
        for metric_type, score in metric_scores.items():
            if score < 0.60:
                priority = "high" if score < 0.40 else "medium"
                training_need = self.db_manager.add_training_need(
                    employee_id=employee_id,
                    skill_category="technical",
                    skill_name=f"{metric_type.replace('_', ' ').title()} Skills",
                    priority=priority,
                    identified_reason=f"Low performance in {metric_type} (score: {score:.2f})",
                    current_level="below_target",
                    target_level="meets_target",
                )
                training_needs.append(training_need)

        if goal_summary.get("overdue", 0) > 0:
            training_need = self.db_manager.add_training_need(
                employee_id=employee_id,
                skill_category="soft_skills",
                skill_name="Time Management",
                priority="high",
                identified_reason=f"{goal_summary.get('overdue', 0)} overdue goals",
                current_level="needs_improvement",
                target_level="proficient",
            )
            training_needs.append(training_need)

        if goal_summary.get("average_completion", 0) < 0.70:
            training_need = self.db_manager.add_training_need(
                employee_id=employee_id,
                skill_category="soft_skills",
                skill_name="Goal Achievement",
                priority="medium",
                identified_reason=f"Low goal completion rate ({goal_summary.get('average_completion', 0):.1f}%)",
                current_level="developing",
                target_level="proficient",
            )
            training_needs.append(training_need)

        logger.info(
            f"Identified {len(training_needs)} training needs for employee {employee_id}",
            extra={"employee_id": employee_id, "training_needs_count": len(training_needs)},
        )

        return training_needs

    def create_development_plan(
        self,
        employee_id: int,
        title: Optional[str] = None,
        duration_months: Optional[int] = None,
    ) -> DevelopmentPlan:
        """Create development plan for employee.

        Args:
            employee_id: Employee ID.
            title: Optional plan title.
            duration_months: Optional plan duration in months.

        Returns:
            DevelopmentPlan object.
        """
        employee = (
            self.db_manager.get_session()
            .query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )

        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        training_needs = self.db_manager.get_unaddressed_training_needs(employee_id=employee_id)

        if not training_needs:
            raise ValueError(f"No training needs identified for employee {employee_id}")

        if duration_months is None:
            duration_months = self.development_config.get("plan_duration_months", 12)

        start_date = date.today()
        end_date = start_date.replace(month=start_date.month + duration_months) if start_date.month + duration_months <= 12 else start_date.replace(year=start_date.year + 1, month=(start_date.month + duration_months) % 12)

        if title is None:
            title = f"Development Plan for {employee.name}"

        objectives = []
        milestones = []
        resources = []

        for training_need in training_needs[:5]:
            objectives.append(f"Improve {training_need.skill_name} from {training_need.current_level} to {training_need.target_level}")

            if self.development_config.get("include_milestones", True):
                milestones.append(f"Complete {training_need.skill_name} training by {start_date.replace(month=start_date.month + 3)}")

            resources.append(f"{training_need.skill_category.replace('_', ' ').title()} training resources for {training_need.skill_name}")

        plan_id = f"{employee.employee_id}_devplan_{start_date.strftime('%Y%m%d')}"

        plan = self.db_manager.add_development_plan(
            employee_id=employee_id,
            plan_id=plan_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            description=f"Comprehensive development plan addressing {len(training_needs)} training needs",
            objectives="\n".join(objectives),
            milestones="\n".join(milestones) if milestones else None,
            resources="\n".join(resources) if resources else None,
        )

        logger.info(
            f"Created development plan for employee {employee_id}",
            extra={
                "employee_id": employee_id,
                "plan_id": plan_id,
                "training_needs_addressed": len(training_needs),
            },
        )

        return plan
