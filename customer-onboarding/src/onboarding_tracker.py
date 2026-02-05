"""Onboarding progress tracking and metrics calculation."""

import logging
from datetime import datetime
from typing import Optional

from src.database import DatabaseManager, Customer, OnboardingStep

logger = logging.getLogger(__name__)


class OnboardingTracker:
    """Tracks onboarding progress and calculates completion metrics."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize onboarding tracker.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    def initialize_steps(
        self, customer_id: int, step_configs: list[dict]
    ) -> list[OnboardingStep]:
        """Initialize onboarding steps for a customer.

        Args:
            customer_id: Customer ID.
            step_configs: List of step configurations with name, order, required.

        Returns:
            List of created OnboardingStep objects.
        """
        steps = []
        with self.db_manager.get_session() as session:
            for step_config in step_configs:
                step = OnboardingStep(
                    customer_id=customer_id,
                    step_name=step_config["name"],
                    step_order=step_config["order"],
                )
                session.add(step)
                steps.append(step)

            session.commit()

            for step in steps:
                session.refresh(step)

        logger.info(
            f"Initialized {len(steps)} onboarding steps for customer {customer_id}",
            extra={"customer_id": customer_id, "step_count": len(steps)},
        )

        return steps

    def complete_step(self, customer_id: int, step_name: str) -> bool:
        """Mark an onboarding step as completed.

        Args:
            customer_id: Customer ID.
            step_name: Name of step to mark as completed.

        Returns:
            True if step was found and marked, False otherwise.
        """
        with self.db_manager.get_session() as session:
            step = (
                session.query(OnboardingStep)
                .filter(
                    OnboardingStep.customer_id == customer_id,
                    OnboardingStep.step_name == step_name,
                )
                .first()
            )

            if not step:
                logger.warning(
                    f"Step {step_name} not found for customer {customer_id}",
                    extra={"customer_id": customer_id, "step_name": step_name},
                )
                return False

            step.is_completed = True
            step.completed_at = datetime.utcnow()
            session.commit()

            logger.info(
                f"Step {step_name} completed for customer {customer_id}",
                extra={"customer_id": customer_id, "step_name": step_name},
            )

            self._update_completion_percentage(customer_id)
            return True

    def _update_completion_percentage(self, customer_id: int) -> None:
        """Calculate and update customer completion percentage.

        Args:
            customer_id: Customer ID.
        """
        with self.db_manager.get_session() as session:
            total_steps = session.query(OnboardingStep).filter(
                OnboardingStep.customer_id == customer_id
            ).count()

            completed_steps = (
                session.query(OnboardingStep)
                .filter(
                    OnboardingStep.customer_id == customer_id,
                    OnboardingStep.is_completed == True,
                )
                .count()
            )

            if total_steps > 0:
                completion_percentage = completed_steps / total_steps
            else:
                completion_percentage = 0.0

            self.db_manager.update_customer_completion(
                customer_id, completion_percentage
            )

            logger.debug(
                f"Updated completion for customer {customer_id}: {completion_percentage:.2%}",
                extra={
                    "customer_id": customer_id,
                    "completed": completed_steps,
                    "total": total_steps,
                    "percentage": completion_percentage,
                },
            )

    def get_completion_metrics(self, customer_id: int) -> dict:
        """Get detailed completion metrics for a customer.

        Args:
            customer_id: Customer ID.

        Returns:
            Dictionary with completion metrics.
        """
        with self.db_manager.get_session() as session:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {}

            steps = (
                session.query(OnboardingStep)
                .filter(OnboardingStep.customer_id == customer_id)
                .order_by(OnboardingStep.step_order)
                .all()
            )

            completed_steps = [s for s in steps if s.is_completed]
            pending_steps = [s for s in steps if not s.is_completed]

            return {
                "customer_id": customer_id,
                "email": customer.email,
                "completion_percentage": customer.completion_percentage,
                "total_steps": len(steps),
                "completed_steps": len(completed_steps),
                "pending_steps": len(pending_steps),
                "onboarding_started_at": customer.onboarding_started_at.isoformat()
                if customer.onboarding_started_at
                else None,
                "onboarding_completed_at": customer.onboarding_completed_at.isoformat()
                if customer.onboarding_completed_at
                else None,
                "steps": [
                    {
                        "name": s.step_name,
                        "order": s.step_order,
                        "completed": s.is_completed,
                        "completed_at": s.completed_at.isoformat()
                        if s.completed_at
                        else None,
                    }
                    for s in steps
                ],
            }

    def get_all_metrics(self, completion_threshold: float = 0.75) -> dict:
        """Get aggregated metrics for all customers.

        Args:
            completion_threshold: Minimum completion percentage for inclusion.

        Returns:
            Dictionary with aggregated metrics.
        """
        with self.db_manager.get_session() as session:
            all_customers = session.query(Customer).filter(Customer.is_active == True).all()

            total_customers = len(all_customers)
            completed_customers = sum(
                1 for c in all_customers if c.completion_percentage >= completion_threshold
            )
            in_progress_customers = total_customers - completed_customers

            avg_completion = (
                sum(c.completion_percentage for c in all_customers) / total_customers
                if total_customers > 0
                else 0.0
            )

            return {
                "total_customers": total_customers,
                "completed_customers": completed_customers,
                "in_progress_customers": in_progress_customers,
                "average_completion_percentage": avg_completion,
                "completion_threshold": completion_threshold,
            }
