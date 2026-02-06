"""Test suite for portfolio generator system."""

import pytest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Investor,
    Portfolio,
    Holding,
    FinancialGoal,
)
from src.portfolio_generator import PortfolioGenerator
from src.risk_analyzer import RiskAnalyzer
from src.goal_calculator import GoalCalculator
from src.rebalancing_engine import RebalancingEngine


@pytest.fixture
def test_db():
    """Create test database."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    return db_manager


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "portfolio": {
            "default_currency": "USD",
            "rebalancing_threshold": 0.05,
        },
        "risk_tolerance": {
            "conservative_allocation": {
                "stocks": 0.30,
                "bonds": 0.50,
                "cash": 0.20,
            },
            "moderate_allocation": {
                "stocks": 0.60,
                "bonds": 0.30,
                "cash": 0.10,
            },
        },
        "asset_classes": {
            "stocks": ["large_cap", "mid_cap"],
            "bonds": ["government", "corporate"],
        },
        "rebalancing": {
            "enabled": True,
            "drift_threshold": 0.05,
        },
        "optimization": {
            "risk_free_rate": 0.02,
        },
    }


@pytest.fixture
def sample_investor(test_db):
    """Create sample investor for testing."""
    investor = test_db.add_investor(
        investor_id="INV001",
        name="Test Investor",
        email="test@example.com",
        risk_tolerance="moderate",
        age=35,
        investment_horizon_years=20,
    )
    return investor


@pytest.fixture
def sample_portfolio(test_db, sample_investor):
    """Create sample portfolio for testing."""
    portfolio = test_db.add_portfolio(
        investor_id=sample_investor.id,
        name="Test Portfolio",
        risk_tolerance="moderate",
    )
    return portfolio


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            investors = session.query(Investor).all()
            assert len(investors) == 0
        finally:
            session.close()

    def test_add_investor(self, test_db):
        """Test adding investor."""
        investor = test_db.add_investor(
            investor_id="INV001",
            name="John Doe",
            email="john@example.com",
            risk_tolerance="moderate",
        )
        assert investor.id is not None
        assert investor.investor_id == "INV001"

    def test_add_portfolio(self, test_db, sample_investor):
        """Test adding portfolio."""
        portfolio = test_db.add_portfolio(
            investor_id=sample_investor.id,
            name="My Portfolio",
            risk_tolerance="moderate",
        )
        assert portfolio.id is not None
        assert portfolio.investor_id == sample_investor.id

    def test_add_holding(self, test_db, sample_portfolio):
        """Test adding holding."""
        holding = test_db.add_holding(
            portfolio_id=sample_portfolio.id,
            asset_symbol="STOCK1",
            asset_name="Stock 1",
            asset_class="stocks",
            target_allocation=0.5,
        )
        assert holding.id is not None
        assert holding.target_allocation == 0.5


class TestPortfolioGenerator:
    """Test portfolio generator functionality."""

    def test_generate_portfolio(self, test_db, sample_config, sample_investor):
        """Test portfolio generation."""
        generator = PortfolioGenerator(test_db, sample_config)
        portfolio = generator.generate_portfolio(
            investor_id=sample_investor.id,
            portfolio_name="Test Portfolio",
            initial_investment=10000.0,
        )

        assert portfolio.id is not None
        assert portfolio.total_value == 10000.0

    def test_get_risk_allocation(self, test_db, sample_config):
        """Test risk allocation retrieval."""
        generator = PortfolioGenerator(test_db, sample_config)
        allocation = generator._get_risk_allocation("conservative")

        assert "stocks" in allocation
        assert "bonds" in allocation


class TestRiskAnalyzer:
    """Test risk analyzer functionality."""

    def test_analyze_risk_tolerance(self, test_db, sample_config, sample_investor):
        """Test risk tolerance analysis."""
        analyzer = RiskAnalyzer(test_db, sample_config)
        result = analyzer.analyze_risk_tolerance(sample_investor.id)

        assert "recommended_risk_tolerance" in result
        assert "recommended_allocation" in result


class TestGoalCalculator:
    """Test goal calculator functionality."""

    def test_calculate_portfolio_requirements(self, test_db, sample_config, sample_investor):
        """Test portfolio requirements calculation."""
        goal = test_db.add_goal(
            investor_id=sample_investor.id,
            goal_type="retirement",
            target_amount=1000000.0,
            target_date=date.today().replace(year=date.today().year + 20),
        )

        calculator = GoalCalculator(test_db, sample_config)
        result = calculator.calculate_portfolio_requirements(sample_investor.id)

        assert "total_required_investment" in result
        assert len(result.get("goals", [])) > 0


class TestRebalancingEngine:
    """Test rebalancing engine functionality."""

    def test_check_rebalancing_needed(self, test_db, sample_config, sample_portfolio):
        """Test rebalancing check."""
        test_db.add_holding(
            portfolio_id=sample_portfolio.id,
            asset_symbol="STOCK1",
            asset_name="Stock 1",
            asset_class="stocks",
            target_allocation=0.5,
            market_value=7000.0,
        )
        test_db.add_holding(
            portfolio_id=sample_portfolio.id,
            asset_symbol="BOND1",
            asset_name="Bond 1",
            asset_class="bonds",
            target_allocation=0.5,
            market_value=3000.0,
        )

        engine = RebalancingEngine(test_db, sample_config)
        needs_rebalancing = engine.check_rebalancing_needed(sample_portfolio.id)

        assert isinstance(needs_rebalancing, bool)


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "portfolio" in config
            assert "risk_tolerance" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
