"""Test suite for performance monitor system."""

import pytest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Employee,
    PerformanceMetric,
    Goal,
    PerformanceReview,
    TrainingNeed,
)
from src.performance_monitor import PerformanceMonitor
from src.goal_tracker import GoalTracker
from src.training_analyzer import TrainingAnalyzer


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
        "performance": {
            "metrics": ["productivity", "quality", "attendance"],
            "evaluation_period_days": 90,
            "performance_thresholds": {
                "excellent": 0.90,
                "good": 0.75,
                "satisfactory": 0.60,
            },
        },
        "goals": {
            "overdue_threshold_days": 7,
        },
        "training": {
            "skill_categories": ["technical", "soft_skills"],
        },
        "development_plans": {
            "plan_duration_months": 12,
        },
    }


@pytest.fixture
def sample_employee(test_db):
    """Create sample employee for testing."""
    employee = test_db.add_employee(
        employee_id="EMP001",
        name="Test Employee",
        email="test@example.com",
        department="Engineering",
        position="Software Engineer",
    )
    return employee


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            employees = session.query(Employee).all()
            assert len(employees) == 0
        finally:
            session.close()

    def test_add_employee(self, test_db):
        """Test adding employee."""
        employee = test_db.add_employee(
            employee_id="EMP001",
            name="John Doe",
            email="john@example.com",
        )
        assert employee.id is not None
        assert employee.employee_id == "EMP001"

    def test_add_metric(self, test_db, sample_employee):
        """Test adding metric."""
        metric = test_db.add_metric(
            employee_id=sample_employee.id,
            metric_type="productivity",
            metric_date=date.today(),
            value=85.0,
            target_value=80.0,
        )
        assert metric.id is not None
        assert metric.value == 85.0


class TestPerformanceMonitor:
    """Test performance monitor functionality."""

    def test_calculate_performance_score(self, test_db, sample_config, sample_employee):
        """Test performance score calculation."""
        test_db.add_metric(
            employee_id=sample_employee.id,
            metric_type="productivity",
            metric_date=date.today(),
            value=85.0,
            target_value=80.0,
        )

        monitor = PerformanceMonitor(test_db, sample_config)
        score = monitor.calculate_performance_score(sample_employee.id)

        assert "overall_score" in score
        assert "rating" in score


class TestGoalTracker:
    """Test goal tracker functionality."""

    def test_update_goal_progress(self, test_db, sample_config, sample_employee):
        """Test goal progress update."""
        goal = test_db.add_goal(
            employee_id=sample_employee.id,
            goal_id="GOAL001",
            title="Test Goal",
            goal_type="quantitative",
            start_date=date.today(),
            due_date=date.today().replace(day=date.today().day + 30),
            target_value=100.0,
        )

        tracker = GoalTracker(test_db, sample_config)
        updated_goal = tracker.update_goal_progress(goal.goal_id, current_value=75.0)

        assert updated_goal.completion_percentage == 75.0


class TestTrainingAnalyzer:
    """Test training analyzer functionality."""

    def test_identify_training_needs(self, test_db, sample_config, sample_employee):
        """Test training needs identification."""
        test_db.add_metric(
            employee_id=sample_employee.id,
            metric_type="productivity",
            metric_date=date.today(),
            value=50.0,
            target_value=80.0,
        )

        analyzer = TrainingAnalyzer(test_db, sample_config)
        training_needs = analyzer.identify_training_needs(sample_employee.id)

        assert isinstance(training_needs, list)


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "performance" in config
            assert "goals" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
