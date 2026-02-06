"""Analyzes risk tolerance and calculates appropriate allocations."""

import logging
from typing import Dict, Optional

from src.database import DatabaseManager, Investor

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Analyzes risk tolerance and calculates asset allocations."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize risk analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.risk_config = config.get("risk_tolerance", {})

    def analyze_risk_tolerance(
        self,
        investor_id: int,
    ) -> Dict:
        """Analyze investor's risk tolerance.

        Args:
            investor_id: Investor ID.

        Returns:
            Dictionary with risk analysis results.
        """
        investor = (
            self.db_manager.get_session()
            .query(Investor)
            .filter(Investor.id == investor_id)
            .first()
        )

        if not investor:
            return {"error": "Investor not found"}

        risk_score = self._calculate_risk_score(investor)
        recommended_tolerance = self._recommend_risk_tolerance(risk_score, investor)

        allocation = self._get_allocation_for_tolerance(recommended_tolerance)

        return {
            "investor_id": investor_id,
            "current_risk_tolerance": investor.risk_tolerance,
            "risk_score": risk_score,
            "recommended_risk_tolerance": recommended_tolerance,
            "recommended_allocation": allocation,
        }

    def _calculate_risk_score(self, investor: Investor) -> float:
        """Calculate risk score for investor.

        Args:
            investor: Investor object.

        Returns:
            Risk score (0.0 to 1.0).
        """
        score = 0.5

        if investor.age:
            if investor.age < 30:
                score += 0.2
            elif investor.age < 50:
                score += 0.1
            elif investor.age >= 65:
                score -= 0.2

        if investor.investment_horizon_years:
            if investor.investment_horizon_years >= 10:
                score += 0.2
            elif investor.investment_horizon_years >= 5:
                score += 0.1
            elif investor.investment_horizon_years < 2:
                score -= 0.2

        tolerance_map = {"conservative": 0.2, "moderate": 0.5, "aggressive": 0.8}
        score = (score + tolerance_map.get(investor.risk_tolerance, 0.5)) / 2.0

        return max(0.0, min(1.0, score))

    def _recommend_risk_tolerance(
        self, risk_score: float, investor: Investor
    ) -> str:
        """Recommend risk tolerance based on score.

        Args:
            risk_score: Calculated risk score.
            investor: Investor object.

        Returns:
            Recommended risk tolerance level.
        """
        if risk_score >= 0.7:
            return "aggressive"
        elif risk_score >= 0.4:
            return "moderate"
        else:
            return "conservative"

    def _get_allocation_for_tolerance(self, risk_tolerance: str) -> Dict[str, float]:
        """Get asset allocation for risk tolerance.

        Args:
            risk_tolerance: Risk tolerance level.

        Returns:
            Dictionary mapping asset classes to allocation percentages.
        """
        allocation_key = f"{risk_tolerance}_allocation"
        return self.risk_config.get(allocation_key, {})
