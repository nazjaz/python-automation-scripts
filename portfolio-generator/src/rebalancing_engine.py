"""Generates rebalancing recommendations for portfolios."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Portfolio, Holding, RebalancingRecommendation

logger = logging.getLogger(__name__)


class RebalancingEngine:
    """Generates rebalancing recommendations for portfolios."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize rebalancing engine.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.rebalancing_config = config.get("rebalancing", {})
        self.drift_threshold = self.rebalancing_config.get("drift_threshold", 0.05)
        self.min_rebalance_amount = self.rebalancing_config.get("min_rebalance_amount", 100.0)

    def check_rebalancing_needed(
        self,
        portfolio_id: int,
    ) -> bool:
        """Check if portfolio needs rebalancing.

        Args:
            portfolio_id: Portfolio ID.

        Returns:
            True if rebalancing is needed, False otherwise.
        """
        portfolio = (
            self.db_manager.get_session()
            .query(Portfolio)
            .filter(Portfolio.id == portfolio_id)
            .first()
        )

        if not portfolio:
            return False

        if not self.rebalancing_config.get("enabled", True):
            return False

        if portfolio.last_rebalanced_at:
            days_since_rebalance = (datetime.utcnow() - portfolio.last_rebalanced_at).days
            rebalancing_frequency = self.config.get("portfolio", {}).get("rebalancing_frequency_days", 90)

            if days_since_rebalance < rebalancing_frequency:
                return False

        holdings = portfolio.holdings
        if not holdings:
            return False

        total_value = sum(h.market_value or 0.0 for h in holdings)
        if total_value == 0:
            return False

        for holding in holdings:
            current_allocation = (holding.market_value or 0.0) / total_value if total_value > 0 else 0.0
            drift = abs(current_allocation - holding.target_allocation)

            if drift > self.drift_threshold:
                return True

        return False

    def generate_rebalancing_recommendations(
        self,
        portfolio_id: int,
    ) -> List[RebalancingRecommendation]:
        """Generate rebalancing recommendations for portfolio.

        Args:
            portfolio_id: Portfolio ID.

        Returns:
            List of RebalancingRecommendation objects.
        """
        portfolio = (
            self.db_manager.get_session()
            .query(Portfolio)
            .filter(Portfolio.id == portfolio_id)
            .first()
        )

        if not portfolio:
            return []

        holdings = portfolio.holdings
        if not holdings:
            return []

        total_value = sum(h.market_value or 0.0 for h in holdings)
        if total_value == 0:
            return []

        recommendations = []

        for holding in holdings:
            current_allocation = (holding.market_value or 0.0) / total_value if total_value > 0 else 0.0
            target_allocation = holding.target_allocation
            drift = current_allocation - target_allocation

            if abs(drift) > self.drift_threshold:
                target_value = total_value * target_allocation
                current_value = holding.market_value or 0.0
                amount_change = target_value - current_value

                if abs(amount_change) >= self.min_rebalance_amount:
                    if amount_change > 0:
                        action_type = "buy"
                        recommended_action = f"Buy ${abs(amount_change):.2f} of {holding.asset_symbol}"
                        priority = "high" if abs(drift) > 0.10 else "medium"
                    else:
                        action_type = "sell"
                        recommended_action = f"Sell ${abs(amount_change):.2f} of {holding.asset_symbol}"
                        priority = "high" if abs(drift) > 0.10 else "medium"

                    recommendation = self.db_manager.add_rebalancing_recommendation(
                        portfolio_id=portfolio_id,
                        action_type=action_type,
                        asset_symbol=holding.asset_symbol,
                        recommended_action=recommended_action,
                        current_allocation=current_allocation,
                        target_allocation=target_allocation,
                        amount_change=amount_change,
                        priority=priority,
                    )

                    recommendations.append(recommendation)

        if recommendations:
            portfolio.last_rebalanced_at = datetime.utcnow()
            session = self.db_manager.get_session()
            try:
                session.merge(portfolio)
                session.commit()
            finally:
                session.close()

        logger.info(
            f"Generated {len(recommendations)} rebalancing recommendations",
            extra={"portfolio_id": portfolio_id, "recommendation_count": len(recommendations)},
        )

        return recommendations

    def apply_rebalancing(
        self,
        portfolio_id: int,
        recommendation_ids: Optional[List[int]] = None,
    ) -> Dict:
        """Apply rebalancing recommendations.

        Args:
            portfolio_id: Portfolio ID.
            recommendation_ids: Optional list of recommendation IDs to apply.

        Returns:
            Dictionary with rebalancing results.
        """
        if recommendation_ids:
            recommendations = [
                self.db_manager.get_session()
                .query(RebalancingRecommendation)
                .filter(
                    RebalancingRecommendation.id == rec_id,
                    RebalancingRecommendation.portfolio_id == portfolio_id,
                )
                .first()
                for rec_id in recommendation_ids
            ]
            recommendations = [r for r in recommendations if r]
        else:
            recommendations = self.db_manager.get_unimplemented_recommendations(portfolio_id=portfolio_id)

        applied_count = 0

        for recommendation in recommendations:
            recommendation.implemented = True
            session = self.db_manager.get_session()
            try:
                session.merge(recommendation)
                session.commit()
            finally:
                session.close()
            applied_count += 1

        logger.info(
            f"Applied {applied_count} rebalancing recommendations",
            extra={"portfolio_id": portfolio_id, "applied_count": applied_count},
        )

        return {
            "success": True,
            "applied_count": applied_count,
        }
