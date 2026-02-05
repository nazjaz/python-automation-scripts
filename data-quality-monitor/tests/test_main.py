"""Unit tests for data quality monitoring automation."""

import pytest
from unittest.mock import MagicMock, patch

from src.database_connector import DatabaseConnector
from src.quality_checks import CompletenessChecker, UniquenessChecker, AccuracyChecker
from src.integrity_validator import IntegrityValidator
from src.scorecard_generator import Scorecard, ScorecardGenerator
from src.remediation_planner import RemediationPlanner


@pytest.fixture
def mock_connector():
    """Create mock database connector."""
    connector = MagicMock(spec=DatabaseConnector)
    connector.name = "test_db"
    connector.db_type = "postgresql"
    connector.get_row_count.return_value = 100
    connector.execute_query.return_value = [{"count": 5}]
    connector.get_table_columns.return_value = [
        {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
        {"name": "email", "type": "VARCHAR", "nullable": False, "primary_key": False},
    ]
    connector.get_foreign_keys.return_value = []
    return connector


@pytest.fixture
def sample_config():
    """Create sample configuration."""
    return {
        "threshold": 0.95,
        "check_null_percentage": True,
        "check_empty_strings": True,
    }


class TestCompletenessChecker:
    """Tests for CompletenessChecker class."""

    def test_check_table_empty_table(self, mock_connector, sample_config):
        """Test completeness check on empty table."""
        checker = CompletenessChecker(mock_connector, sample_config)
        mock_connector.get_row_count.return_value = 0

        result = checker.check_table("test_table")

        assert result.score == 0.0
        assert result.passed is False
        assert len(result.issues) > 0
        assert result.issues[0]["type"] == "empty_table"

    def test_check_table_with_nulls(self, mock_connector, sample_config):
        """Test completeness check with NULL values."""
        checker = CompletenessChecker(mock_connector, sample_config)
        mock_connector.get_row_count.return_value = 100
        mock_connector.execute_query.return_value = [{"null_count": 10}]

        result = checker.check_table("test_table", ["email"])

        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_table_passed(self, mock_connector, sample_config):
        """Test completeness check that passes threshold."""
        checker = CompletenessChecker(mock_connector, sample_config)
        mock_connector.get_row_count.return_value = 100
        mock_connector.execute_query.return_value = [{"null_count": 0}]

        result = checker.check_table("test_table", ["email"])

        assert result.score >= sample_config["threshold"]


class TestUniquenessChecker:
    """Tests for UniquenessChecker class."""

    def test_check_table_no_duplicates(self, mock_connector):
        """Test uniqueness check with no duplicates."""
        config = {"threshold": 0.98, "check_duplicate_records": True}
        checker = UniquenessChecker(mock_connector, config)
        mock_connector.get_row_count.return_value = 100
        mock_connector.execute_query.return_value = []

        result = checker.check_table("test_table", ["email"])

        assert result.score >= config["threshold"]
        assert result.passed is True

    def test_check_table_with_duplicates(self, mock_connector):
        """Test uniqueness check with duplicates."""
        config = {"threshold": 0.98, "check_duplicate_records": True}
        checker = UniquenessChecker(mock_connector, config)
        mock_connector.get_row_count.return_value = 100
        mock_connector.execute_query.return_value = [
            {"email": "test@example.com", "count": 2}
        ]

        result = checker.check_table("test_table", ["email"])

        assert len(result.issues) > 0


class TestAccuracyChecker:
    """Tests for AccuracyChecker class."""

    def test_check_table_pattern_validation(self, mock_connector):
        """Test accuracy check with pattern validation."""
        config = {"threshold": 0.85, "check_pattern_matching": True}
        checker = AccuracyChecker(mock_connector, config)
        mock_connector.get_row_count.return_value = 100
        mock_connector.execute_query.return_value = [{"invalid_count": 5}]

        column_checks = [
            {"name": "email", "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
        ]

        result = checker.check_table("test_table", column_checks)

        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_check_table_range_validation(self, mock_connector):
        """Test accuracy check with range validation."""
        config = {"threshold": 0.85, "check_range_validation": True}
        checker = AccuracyChecker(mock_connector, config)
        mock_connector.get_row_count.return_value = 100
        mock_connector.execute_query.return_value = [{"invalid_count": 3}]

        column_checks = [{"name": "age", "min": 0, "max": 150}]

        result = checker.check_table("test_table", column_checks)

        assert result.score >= 0.0
        assert result.score <= 1.0


class TestScorecard:
    """Tests for Scorecard class."""

    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        scorecard = Scorecard("test_db")

        from src.quality_checks import QualityCheckResult

        results = [
            QualityCheckResult(
                check_type="completeness",
                table_name="test_table",
                column_name=None,
                score=0.95,
                passed=True,
                issues=[],
                threshold=0.95,
            ),
            QualityCheckResult(
                check_type="uniqueness",
                table_name="test_table",
                column_name=None,
                score=0.98,
                passed=True,
                issues=[],
                threshold=0.98,
            ),
        ]

        scorecard.add_table_result("test_table", results)
        overall_score = scorecard.calculate_overall_score()

        assert overall_score >= 0.0
        assert overall_score <= 1.0

    def test_add_integrity_issues(self):
        """Test adding integrity issues to scorecard."""
        scorecard = Scorecard("test_db")

        from src.integrity_validator import IntegrityIssue

        issue = IntegrityIssue(
            issue_type="foreign_key_violation",
            table_name="test_table",
            column_name="user_id",
            description="Foreign key violation",
            severity="critical",
            affected_rows=5,
        )

        scorecard.add_integrity_issues([issue])

        assert len(scorecard.integrity_issues) == 1
        assert scorecard.integrity_issues[0]["severity"] == "critical"


class TestRemediationPlanner:
    """Tests for RemediationPlanner class."""

    def test_create_plan_from_quality_result(self):
        """Test remediation plan creation from quality result."""
        planner = RemediationPlanner()

        from src.quality_checks import QualityCheckResult

        result = QualityCheckResult(
            check_type="completeness",
            table_name="test_table",
            column_name=None,
            score=0.80,
            passed=False,
            issues=[
                {
                    "type": "high_null_percentage",
                    "column": "email",
                    "null_percentage": 0.30,
                    "null_count": 30,
                }
            ],
            threshold=0.95,
        )

        plan = planner.create_plan_from_quality_result(result)

        assert plan.table_name == "test_table"
        assert len(plan.actions) > 0
