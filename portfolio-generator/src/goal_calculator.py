"""Calculates portfolio needs based on financial goals."""

import logging
from datetime import date
from typing import Dict, List, Optional

from src.database import DatabaseManager, FinancialGoal, Investor

logger = logging.getLogger(__name__)


class GoalCalculator:
    """Calculates portfolio requirements based on financial goals."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize goal calculator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.goals_config = config.get("financial_goals", {})
        self.optimization_config = config.get("optimization", {})
        self.risk_free_rate = self.optimization_config.get("risk_free_rate", 0.02)

    def calculate_portfolio_requirements(
        self,
        investor_id: int,
    ) -> Dict:
        """Calculate portfolio requirements for investor's goals.

        Args:
            investor_id: Investor ID.

        Returns:
            Dictionary with portfolio requirements.
        """
        goals = (
            self.db_manager.get_session()
            .query(FinancialGoal)
            .filter(FinancialGoal.investor_id == investor_id)
            .all()
        )

        if not goals:
            return {"error": "No goals found for investor"}

        investor = (
            self.db_manager.get_session()
            .query(Investor)
            .filter(Investor.id == investor_id)
            .first()
        )

        total_required = 0.0
        goal_requirements = []

        for goal in goals:
            years_to_goal = (goal.target_date - date.today()).days / 365.0

            if years_to_goal <= 0:
                required_amount = goal.target_amount - goal.current_amount
            else:
                required_amount = self._calculate_required_investment(
                    goal.target_amount,
                    goal.current_amount,
                    years_to_goal,
                    investor.risk_tolerance if investor else "moderate",
                )

            total_required += required_amount

            goal_requirements.append(
                {
                    "goal_id": goal.id,
                    "goal_type": goal.goal_type,
                    "target_amount": goal.target_amount,
                    "current_amount": goal.current_amount,
                    "years_to_goal": years_to_goal,
                    "required_investment": required_amount,
                }
            )

        return {
            "investor_id": investor_id,
            "total_required_investment": total_required,
            "goals": goal_requirements,
        }

    def _calculate_required_investment(
        self,
        target_amount: float,
        current_amount: float,
        years: float,
        risk_tolerance: str,
    ) -> float:
        """Calculate required investment to reach goal.

        Args:
            target_amount: Target amount.
            current_amount: Current amount.
            years: Years until goal.
            risk_tolerance: Risk tolerance level.

        Returns:
            Required investment amount.
        """
        if years <= 0:
            return max(0.0, target_amount - current_amount)

        expected_return = self._get_expected_return(risk_tolerance)

        if expected_return <= 0:
            return max(0.0, target_amount - current_amount)

        future_value_current = current_amount * ((1 + expected_return) ** years)
        shortfall = target_amount - future_value_current

        if shortfall <= 0:
            return 0.0

        present_value_shortfall = shortfall / ((1 + expected_return) ** years)

        return present_value_shortfall

    def _get_expected_return(self, risk_tolerance: str) -> float:
        """Get expected return for risk tolerance.

        Args:
            risk_tolerance: Risk tolerance level.

        Returns:
            Expected annual return.
        """
        return_map = {
            "conservative": 0.04,
            "moderate": 0.07,
            "aggressive": 0.10,
        }

        return return_map.get(risk_tolerance, 0.07)

    def update_goal_progress(
        self,
        goal_id: int,
        current_amount: float,
    ) -> FinancialGoal:
        """Update goal progress.

        Args:
            goal_id: Goal ID.
            current_amount: Current amount toward goal.

        Returns:
            Updated FinancialGoal object.
        """
        goal = (
            self.db_manager.get_session()
            .query(FinancialGoal)
            .filter(FinancialGoal.id == goal_id)
            .first()
        )

        if goal:
            goal.current_amount = current_amount
            session = self.db_manager.get_session()
            try:
                session.merge(goal)
                session.commit()
                session.refresh(goal)
            finally:
                session.close()

        return goal
