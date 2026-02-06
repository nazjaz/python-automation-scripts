"""Generates personalized investment portfolios."""

import logging
from typing import Dict, List, Optional

from src.database import DatabaseManager, Portfolio, Holding, Investor, FinancialGoal

logger = logging.getLogger(__name__)


class PortfolioGenerator:
    """Generates personalized investment portfolios."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize portfolio generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.portfolio_config = config.get("portfolio", {})
        self.risk_config = config.get("risk_tolerance", {})
        self.asset_classes = config.get("asset_classes", {})

    def generate_portfolio(
        self,
        investor_id: int,
        portfolio_name: str,
        initial_investment: float,
        risk_tolerance: Optional[str] = None,
    ) -> Portfolio:
        """Generate personalized portfolio for investor.

        Args:
            investor_id: Investor ID.
            portfolio_name: Portfolio name.
            initial_investment: Initial investment amount.
            risk_tolerance: Optional risk tolerance (uses investor's if not provided).

        Returns:
            Portfolio object with generated holdings.
        """
        investor = (
            self.db_manager.get_session()
            .query(Investor)
            .filter(Investor.id == investor_id)
            .first()
        )

        if not investor:
            raise ValueError(f"Investor {investor_id} not found")

        risk_tolerance = risk_tolerance or investor.risk_tolerance

        portfolio = self.db_manager.add_portfolio(
            investor_id=investor_id,
            name=portfolio_name,
            risk_tolerance=risk_tolerance,
        )

        allocation = self._get_risk_allocation(risk_tolerance)
        holdings = self._generate_holdings(
            portfolio_id=portfolio.id,
            total_value=initial_investment,
            allocation=allocation,
        )

        portfolio.total_value = initial_investment
        session = self.db_manager.get_session()
        try:
            session.merge(portfolio)
            session.commit()
        finally:
            session.close()

        logger.info(
            f"Generated portfolio for investor {investor_id}",
            extra={
                "portfolio_id": portfolio.id,
                "investor_id": investor_id,
                "total_value": initial_investment,
                "holdings_count": len(holdings),
            },
        )

        return portfolio

    def _get_risk_allocation(self, risk_tolerance: str) -> Dict[str, float]:
        """Get asset allocation based on risk tolerance.

        Args:
            risk_tolerance: Risk tolerance level.

        Returns:
            Dictionary mapping asset classes to allocation percentages.
        """
        allocation_key = f"{risk_tolerance}_allocation"
        allocation = self.risk_config.get(allocation_key, {})

        if not allocation:
            allocation = self.risk_config.get("moderate_allocation", {})

        return allocation

    def _generate_holdings(
        self,
        portfolio_id: int,
        total_value: float,
        allocation: Dict[str, float],
    ) -> List[Holding]:
        """Generate holdings based on allocation.

        Args:
            portfolio_id: Portfolio ID.
            total_value: Total portfolio value.
            allocation: Asset allocation dictionary.

        Returns:
            List of Holding objects.
        """
        holdings = []

        stocks_allocation = allocation.get("stocks", 0.0)
        bonds_allocation = allocation.get("bonds", 0.0)
        cash_allocation = allocation.get("cash", 0.0)

        stock_types = self.asset_classes.get("stocks", [])
        bond_types = self.asset_classes.get("bonds", [])

        if stocks_allocation > 0 and stock_types:
            per_stock_allocation = stocks_allocation / len(stock_types)
            for stock_type in stock_types:
                holding = self.db_manager.add_holding(
                    portfolio_id=portfolio_id,
                    asset_symbol=f"STOCK_{stock_type.upper()}",
                    asset_name=f"{stock_type.replace('_', ' ').title()} Stock",
                    asset_class="stocks",
                    asset_type=stock_type,
                    target_allocation=per_stock_allocation,
                )
                holdings.append(holding)

        if bonds_allocation > 0 and bond_types:
            per_bond_allocation = bonds_allocation / len(bond_types)
            for bond_type in bond_types:
                holding = self.db_manager.add_holding(
                    portfolio_id=portfolio_id,
                    asset_symbol=f"BOND_{bond_type.upper()}",
                    asset_name=f"{bond_type.replace('_', ' ').title()} Bond",
                    asset_class="bonds",
                    asset_type=bond_type,
                    target_allocation=per_bond_allocation,
                )
                holdings.append(holding)

        if cash_allocation > 0:
            holding = self.db_manager.add_holding(
                portfolio_id=portfolio_id,
                asset_symbol="CASH",
                asset_name="Cash",
                asset_class="cash",
                target_allocation=cash_allocation,
            )
            holdings.append(holding)

        return holdings

    def generate_goal_based_portfolio(
        self,
        investor_id: int,
        goal_id: int,
        portfolio_name: str,
    ) -> Portfolio:
        """Generate portfolio based on financial goal.

        Args:
            investor_id: Investor ID.
            goal_id: Financial goal ID.
            portfolio_name: Portfolio name.

        Returns:
            Portfolio object.
        """
        goal = (
            self.db_manager.get_session()
            .query(FinancialGoal)
            .filter(FinancialGoal.id == goal_id, FinancialGoal.investor_id == investor_id)
            .first()
        )

        if not goal:
            raise ValueError(f"Goal {goal_id} not found for investor {investor_id}")

        investor = (
            self.db_manager.get_session()
            .query(Investor)
            .filter(Investor.id == investor_id)
            .first()
        )

        from datetime import date
        from dateutil.relativedelta import relativedelta

        years_to_goal = (goal.target_date - date.today()).days / 365.0

        risk_tolerance = investor.risk_tolerance

        if years_to_goal < 1:
            risk_tolerance = "conservative"
        elif years_to_goal < 5:
            risk_tolerance = "moderate"
        else:
            risk_tolerance = investor.risk_tolerance

        portfolio = self.generate_portfolio(
            investor_id=investor_id,
            portfolio_name=portfolio_name,
            initial_investment=goal.current_amount,
            risk_tolerance=risk_tolerance,
        )

        logger.info(
            f"Generated goal-based portfolio",
            extra={
                "portfolio_id": portfolio.id,
                "goal_id": goal_id,
                "goal_type": goal.goal_type,
            },
        )

        return portfolio
