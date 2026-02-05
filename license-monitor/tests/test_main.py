"""Unit tests for license monitoring automation."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.database import DatabaseManager, License, ComplianceRecord
from src.license_collector import LicenseCollector
from src.compliance_checker import ComplianceChecker
from src.optimizer import LicenseOptimizer
from src.usage_tracker import UsageTracker
from src.report_generator import ReportGenerator


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    return MagicMock(spec=DatabaseManager)


@pytest.fixture
def sample_license():
    """Create sample license."""
    license_obj = MagicMock(spec=License)
    license_obj.id = 1
    license_obj.license_type = "Microsoft Office"
    license_obj.license_key = "TEST-KEY-123"
    license_obj.assigned_to = "test@example.com"
    license_obj.assigned_email = "test@example.com"
    license_obj.status = "active"
    return license_obj


class TestLicenseCollector:
    """Tests for LicenseCollector class."""

    def test_collect_from_csv(self, mock_db_manager):
        """Test CSV license collection."""
        collector = LicenseCollector(mock_db_manager)

        source_config = {
            "name": "csv_source",
            "type": "csv",
            "enabled": True,
            "file_path": "data/licenses.csv",
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = [
                    "type,key,user,email,cost\n",
                    "Microsoft Office,KEY1,user1,user1@example.com,150.00\n",
                ]

                with patch("csv.DictReader") as mock_reader:
                    mock_reader.return_value = [
                        {
                            "type": "Microsoft Office",
                            "key": "KEY1",
                            "user": "user1",
                            "email": "user1@example.com",
                            "cost": "150.00",
                        }
                    ]

                    result = collector.collect_from_source(source_config, MagicMock())

                    assert result >= 0

    def test_collect_from_api(self, mock_db_manager):
        """Test API license collection."""
        collector = LicenseCollector(mock_db_manager)

        source_config = {
            "name": "api_source",
            "type": "api",
            "enabled": True,
            "api_url": "https://api.example.com",
            "api_key": "test-key",
        }

        settings = MagicMock()
        settings.snow_api_url = "https://api.example.com"
        settings.snow_api_key = "test-key"

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": [
                    {
                        "type": "Microsoft Office",
                        "key": "KEY1",
                        "user": "user1",
                        "email": "user1@example.com",
                        "cost": 150.00,
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = collector.collect_from_source(source_config, settings)

            assert result >= 0


class TestComplianceChecker:
    """Tests for ComplianceChecker class."""

    def test_check_compliance(self, mock_db_manager):
        """Test compliance checking."""
        checker = ComplianceChecker(mock_db_manager, threshold=0.95)

        mock_licenses = [
            MagicMock(assigned_to="user1", status="active"),
            MagicMock(assigned_to="user2", status="active"),
            MagicMock(assigned_to=None, status="active"),
        ]

        mock_db_manager.get_licenses_by_type.return_value = mock_licenses
        mock_db_manager.get_unused_licenses.return_value = []

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        result = checker.check_compliance("Microsoft Office")

        assert result is not None
        assert result.license_type == "Microsoft Office"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestLicenseOptimizer:
    """Tests for LicenseOptimizer class."""

    def test_identify_unused_licenses(self, mock_db_manager):
        """Test unused license identification."""
        license_types_config = [
            {
                "name": "Microsoft Office",
                "cost_per_license": 150.00,
                "category": "productivity",
            }
        ]

        optimizer = LicenseOptimizer(
            mock_db_manager, license_types_config, cost_savings_threshold=100.00
        )

        unused_license = MagicMock()
        unused_license.license_type = "Microsoft Office"
        unused_license.id = 1

        mock_db_manager.get_unused_licenses.return_value = [unused_license]

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        recommendations = optimizer.identify_unused_licenses(threshold_days=90)

        assert len(recommendations) > 0
        assert recommendations[0].recommendation_type == "unused_licenses"


class TestUsageTracker:
    """Tests for UsageTracker class."""

    def test_record_usage(self, mock_db_manager):
        """Test usage recording."""
        tracker = UsageTracker(mock_db_manager)

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        usage = tracker.record_usage(
            license_id=1, user_email="test@example.com", usage_duration_minutes=60
        )

        assert usage is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_usage_stats(self, mock_db_manager):
        """Test usage statistics retrieval."""
        tracker = UsageTracker(mock_db_manager)

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.distinct.return_value = mock_query

        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        stats = tracker.get_usage_stats(license_id=1)

        assert "total_usage_records" in stats
        assert "active_usage" in stats
        assert "unique_users" in stats
