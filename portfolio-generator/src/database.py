"""Database models and operations for portfolio generator data."""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Date,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


class Investor(Base):
    """Database model for investors."""

    __tablename__ = "investors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investor_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    risk_tolerance = Column(String(50), nullable=False, index=True)
    age = Column(Integer)
    investment_horizon_years = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolios = relationship("Portfolio", back_populates="investor", cascade="all, delete-orphan")
    goals = relationship("FinancialGoal", back_populates="investor", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Investor(id={self.id}, investor_id={self.investor_id}, name={self.name})>"


class Portfolio(Base):
    """Database model for investment portfolios."""

    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    total_value = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    risk_tolerance = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_rebalanced_at = Column(DateTime, index=True)

    investor = relationship("Investor", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    rebalancing_recommendations = relationship(
        "RebalancingRecommendation", back_populates="portfolio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Portfolio(id={self.id}, investor_id={self.investor_id}, "
            f"name={self.name}, total_value={self.total_value})>"
        )


class Holding(Base):
    """Database model for portfolio holdings."""

    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    asset_symbol = Column(String(50), nullable=False, index=True)
    asset_name = Column(String(255), nullable=False)
    asset_class = Column(String(100), nullable=False, index=True)
    asset_type = Column(String(100), index=True)
    quantity = Column(Float, default=0.0)
    current_price = Column(Float)
    target_allocation = Column(Float, nullable=False)
    current_allocation = Column(Float)
    market_value = Column(Float, default=0.0)
    purchase_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="holdings")

    def __repr__(self) -> str:
        return (
            f"<Holding(id={self.id}, portfolio_id={self.portfolio_id}, "
            f"asset_symbol={self.asset_symbol}, target_allocation={self.target_allocation})>"
        )


class FinancialGoal(Base):
    """Database model for financial goals."""

    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False, index=True)
    goal_type = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(Date, nullable=False, index=True)
    priority = Column(String(50), default="medium", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    investor = relationship("Investor", back_populates="goals")

    def __repr__(self) -> str:
        return (
            f"<FinancialGoal(id={self.id}, investor_id={self.investor_id}, "
            f"goal_type={self.goal_type}, target_amount={self.target_amount})>"
        )


class MarketCondition(Base):
    """Database model for market conditions."""

    __tablename__ = "market_conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    condition_date = Column(Date, nullable=False, index=True)
    market_type = Column(String(50), nullable=False, index=True)
    volatility_index = Column(Float)
    market_sentiment = Column(String(50))
    interest_rate = Column(Float)
    inflation_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<MarketCondition(id={self.id}, condition_date={self.condition_date}, "
            f"market_type={self.market_type}, volatility_index={self.volatility_index})>"
        )


class RebalancingRecommendation(Base):
    """Database model for rebalancing recommendations."""

    __tablename__ = "rebalancing_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    recommendation_date = Column(DateTime, default=datetime.utcnow, index=True)
    action_type = Column(String(50), nullable=False)
    asset_symbol = Column(String(50), nullable=False)
    current_allocation = Column(Float)
    target_allocation = Column(Float)
    recommended_action = Column(String(100), nullable=False)
    amount_change = Column(Float)
    priority = Column(String(50), default="medium", index=True)
    implemented = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="rebalancing_recommendations")

    def __repr__(self) -> str:
        return (
            f"<RebalancingRecommendation(id={self.id}, portfolio_id={self.portfolio_id}, "
            f"action_type={self.action_type}, asset_symbol={self.asset_symbol})>"
        )


class DatabaseManager:
    """Manages database operations for portfolio generator data."""

    def __init__(self, database_url: str) -> None:
        """Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL.
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get database session.

        Returns:
            SQLAlchemy session object.
        """
        return self.SessionLocal()

    def add_investor(
        self,
        investor_id: str,
        name: str,
        email: str,
        risk_tolerance: str,
        age: Optional[int] = None,
        investment_horizon_years: Optional[int] = None,
    ) -> Investor:
        """Add or update investor.

        Args:
            investor_id: Investor ID.
            name: Investor name.
            email: Investor email.
            risk_tolerance: Risk tolerance level.
            age: Optional age.
            investment_horizon_years: Optional investment horizon in years.

        Returns:
            Investor object.
        """
        session = self.get_session()
        try:
            investor = (
                session.query(Investor)
                .filter(Investor.investor_id == investor_id)
                .first()
            )

            if investor is None:
                investor = Investor(
                    investor_id=investor_id,
                    name=name,
                    email=email,
                    risk_tolerance=risk_tolerance,
                    age=age,
                    investment_horizon_years=investment_horizon_years,
                )
                session.add(investor)
            else:
                investor.name = name
                investor.email = email
                investor.risk_tolerance = risk_tolerance
                investor.age = age
                investor.investment_horizon_years = investment_horizon_years
                investor.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(investor)
            return investor
        finally:
            session.close()

    def add_portfolio(
        self,
        investor_id: int,
        name: str,
        risk_tolerance: str,
        currency: str = "USD",
    ) -> Portfolio:
        """Add portfolio.

        Args:
            investor_id: Investor ID.
            name: Portfolio name.
            risk_tolerance: Risk tolerance level.
            currency: Currency code.

        Returns:
            Portfolio object.
        """
        session = self.get_session()
        try:
            portfolio = Portfolio(
                investor_id=investor_id,
                name=name,
                risk_tolerance=risk_tolerance,
                currency=currency,
            )
            session.add(portfolio)
            session.commit()
            session.refresh(portfolio)
            return portfolio
        finally:
            session.close()

    def add_holding(
        self,
        portfolio_id: int,
        asset_symbol: str,
        asset_name: str,
        asset_class: str,
        target_allocation: float,
        quantity: float = 0.0,
        current_price: Optional[float] = None,
        asset_type: Optional[str] = None,
    ) -> Holding:
        """Add holding to portfolio.

        Args:
            portfolio_id: Portfolio ID.
            asset_symbol: Asset symbol/ticker.
            asset_name: Asset name.
            asset_class: Asset class.
            target_allocation: Target allocation percentage.
            quantity: Optional quantity.
            current_price: Optional current price.
            asset_type: Optional asset type.

        Returns:
            Holding object.
        """
        session = self.get_session()
        try:
            holding = Holding(
                portfolio_id=portfolio_id,
                asset_symbol=asset_symbol,
                asset_name=asset_name,
                asset_class=asset_class,
                target_allocation=target_allocation,
                quantity=quantity,
                current_price=current_price,
                asset_type=asset_type,
            )
            session.add(holding)
            session.commit()
            session.refresh(holding)
            return holding
        finally:
            session.close()

    def add_goal(
        self,
        investor_id: int,
        goal_type: str,
        target_amount: float,
        target_date: date,
        description: Optional[str] = None,
        priority: str = "medium",
    ) -> FinancialGoal:
        """Add financial goal.

        Args:
            investor_id: Investor ID.
            goal_type: Goal type.
            target_amount: Target amount.
            target_date: Target date.
            description: Optional description.
            priority: Priority level.

        Returns:
            FinancialGoal object.
        """
        session = self.get_session()
        try:
            goal = FinancialGoal(
                investor_id=investor_id,
                goal_type=goal_type,
                target_amount=target_amount,
                target_date=target_date,
                description=description,
                priority=priority,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return goal
        finally:
            session.close()

    def add_market_condition(
        self,
        condition_date: date,
        market_type: str,
        volatility_index: Optional[float] = None,
        market_sentiment: Optional[str] = None,
        interest_rate: Optional[float] = None,
        inflation_rate: Optional[float] = None,
    ) -> MarketCondition:
        """Add market condition.

        Args:
            condition_date: Condition date.
            market_type: Market type.
            volatility_index: Optional volatility index.
            market_sentiment: Optional market sentiment.
            interest_rate: Optional interest rate.
            inflation_rate: Optional inflation rate.

        Returns:
            MarketCondition object.
        """
        session = self.get_session()
        try:
            condition = MarketCondition(
                condition_date=condition_date,
                market_type=market_type,
                volatility_index=volatility_index,
                market_sentiment=market_sentiment,
                interest_rate=interest_rate,
                inflation_rate=inflation_rate,
            )
            session.add(condition)
            session.commit()
            session.refresh(condition)
            return condition
        finally:
            session.close()

    def add_rebalancing_recommendation(
        self,
        portfolio_id: int,
        action_type: str,
        asset_symbol: str,
        recommended_action: str,
        current_allocation: Optional[float] = None,
        target_allocation: Optional[float] = None,
        amount_change: Optional[float] = None,
        priority: str = "medium",
    ) -> RebalancingRecommendation:
        """Add rebalancing recommendation.

        Args:
            portfolio_id: Portfolio ID.
            action_type: Action type (buy, sell, rebalance).
            asset_symbol: Asset symbol.
            recommended_action: Recommended action description.
            current_allocation: Optional current allocation.
            target_allocation: Optional target allocation.
            amount_change: Optional amount change.
            priority: Priority level.

        Returns:
            RebalancingRecommendation object.
        """
        session = self.get_session()
        try:
            recommendation = RebalancingRecommendation(
                portfolio_id=portfolio_id,
                action_type=action_type,
                asset_symbol=asset_symbol,
                recommended_action=recommended_action,
                current_allocation=current_allocation,
                target_allocation=target_allocation,
                amount_change=amount_change,
                priority=priority,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_portfolios(
        self,
        investor_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Portfolio]:
        """Get portfolios with optional filtering.

        Args:
            investor_id: Optional investor ID filter.
            limit: Optional limit on number of results.

        Returns:
            List of Portfolio objects.
        """
        session = self.get_session()
        try:
            query = session.query(Portfolio)

            if investor_id:
                query = query.filter(Portfolio.investor_id == investor_id)

            query = query.order_by(Portfolio.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_latest_market_condition(self) -> Optional[MarketCondition]:
        """Get latest market condition.

        Returns:
            MarketCondition object or None.
        """
        session = self.get_session()
        try:
            return (
                session.query(MarketCondition)
                .order_by(MarketCondition.condition_date.desc())
                .first()
            )
        finally:
            session.close()

    def get_unimplemented_recommendations(
        self, portfolio_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[RebalancingRecommendation]:
        """Get unimplemented rebalancing recommendations.

        Args:
            portfolio_id: Optional portfolio ID filter.
            limit: Optional limit on number of results.

        Returns:
            List of unimplemented RebalancingRecommendation objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(RebalancingRecommendation)
                .filter(RebalancingRecommendation.implemented == False)
            )

            if portfolio_id:
                query = query.filter(RebalancingRecommendation.portfolio_id == portfolio_id)

            query = query.order_by(RebalancingRecommendation.recommendation_date.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
