"""Test suite for expense processor system."""

import pytest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Employee,
    ExpenseReport,
    Expense,
    Receipt,
    Policy,
)
from src.expense_validator import ExpenseValidator
from src.reimbursement_calculator import ReimbursementCalculator
from src.approval_router import ApprovalRouter


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
        "expense_policies": {
            "max_daily_meal": 75.0,
            "require_receipt_threshold": 25.0,
            "allowed_categories": ["meals", "lodging"],
        },
        "validation": {
            "check_duplicates": True,
        },
        "reimbursement": {
            "calculation_method": "full",
        },
        "approval": {
            "routing_enabled": True,
            "auto_approve_under": 25.0,
            "approval_levels": [
                {"level": 1, "max_amount": 100.0, "approver_role": "manager"},
            ],
        },
    }


@pytest.fixture
def sample_employee(test_db):
    """Create sample employee for testing."""
    employee = test_db.add_employee(
        employee_id="EMP001",
        name="Test Employee",
        email="test@example.com",
        role="employee",
    )
    return employee


@pytest.fixture
def sample_report(test_db, sample_employee):
    """Create sample expense report for testing."""
    report = test_db.add_expense_report(
        employee_id=sample_employee.id,
        report_date=date.today(),
    )
    return report


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

    def test_add_expense_report(self, test_db, sample_employee):
        """Test adding expense report."""
        report = test_db.add_expense_report(
            employee_id=sample_employee.id,
            report_date=date.today(),
        )
        assert report.id is not None
        assert report.employee_id == sample_employee.id

    def test_add_expense(self, test_db, sample_report):
        """Test adding expense."""
        expense = test_db.add_expense(
            report_id=sample_report.id,
            expense_date=date.today(),
            category="meals",
            amount=50.0,
        )
        assert expense.id is not None
        assert expense.amount == 50.0


class TestExpenseValidator:
    """Test expense validator functionality."""

    def test_validate_expense(self, test_db, sample_config, sample_report):
        """Test expense validation."""
        expense = test_db.add_expense(
            report_id=sample_report.id,
            expense_date=date.today(),
            category="meals",
            amount=50.0,
        )

        validator = ExpenseValidator(test_db, sample_config)
        result = validator.validate_expense(expense.id)

        assert "valid" in result

    def test_validate_report(self, test_db, sample_config, sample_report):
        """Test report validation."""
        test_db.add_expense(
            report_id=sample_report.id,
            expense_date=date.today(),
            category="meals",
            amount=50.0,
        )

        validator = ExpenseValidator(test_db, sample_config)
        result = validator.validate_report(sample_report.id)

        assert "valid" in result
        assert "expenses_validated" in result


class TestReimbursementCalculator:
    """Test reimbursement calculator functionality."""

    def test_calculate_reimbursement(self, test_db, sample_config, sample_report):
        """Test reimbursement calculation."""
        expense = test_db.add_expense(
            report_id=sample_report.id,
            expense_date=date.today(),
            category="meals",
            amount=50.0,
        )
        expense.validated = True

        session = test_db.get_session()
        try:
            session.merge(expense)
            session.commit()
        finally:
            session.close()

        calculator = ReimbursementCalculator(test_db, sample_config)
        result = calculator.calculate_reimbursement(sample_report.id)

        assert "reimbursable_amount" in result
        assert result["reimbursable_amount"] == 50.0


class TestApprovalRouter:
    """Test approval router functionality."""

    def test_route_for_approval(self, test_db, sample_config, sample_report, sample_employee):
        """Test approval routing."""
        manager = test_db.add_employee(
            employee_id="MGR001",
            name="Manager",
            email="manager@example.com",
            role="manager",
        )

        sample_employee.manager_id = manager.id
        session = test_db.get_session()
        try:
            session.merge(sample_employee)
            session.commit()
        finally:
            session.close()

        expense = test_db.add_expense(
            report_id=sample_report.id,
            expense_date=date.today(),
            category="meals",
            amount=50.0,
        )
        expense.validated = True

        session = test_db.get_session()
        try:
            session.merge(expense)
            session.commit()
        finally:
            session.close()

        calculator = ReimbursementCalculator(test_db, sample_config)
        calculator.calculate_reimbursement(sample_report.id)

        router = ApprovalRouter(test_db, sample_config)
        approvals = router.route_for_approval(sample_report.id)

        assert isinstance(approvals, list)


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "expense_policies" in config
            assert "validation" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
