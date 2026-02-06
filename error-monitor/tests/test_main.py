"""Unit tests for error monitoring system."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, ErrorLog, ErrorCategory, ErrorPattern, BugReport
from src.log_parser import LogParser
from src.error_categorizer import ErrorCategorizer
from src.pattern_identifier import PatternIdentifier
from src.error_monitor import ErrorMonitor
from src.bug_report_generator import BugReportGenerator


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "parsing": {
            "log_format": "standard",
            "timestamp_format": "%Y-%m-%d %H:%M:%S",
        },
        "categorization": {
            "categories": {
                "database": {
                    "description": "Database errors",
                    "keywords": ["database", "sql", "connection"],
                    "default_severity": "high",
                },
                "authentication": {
                    "description": "Auth errors",
                    "keywords": ["authentication", "unauthorized"],
                    "default_severity": "high",
                },
            },
            "severity_rules": {
                "keywords": {
                    "critical": ["fatal"],
                    "high": ["error"],
                },
            },
        },
        "pattern_identification": {
            "min_frequency": 3,
            "similarity_threshold": 0.8,
        },
        "monitoring": {
            "time_window_minutes": 60,
            "error_rate_threshold": 1.0,
        },
        "bug_reports": {
            "priority_rules": {},
        },
        "reporting": {
            "generate_html": True,
            "generate_csv": True,
            "output_directory": "reports",
        },
        "logging": {
            "file": "logs/test.log",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def db_manager():
    """Database manager fixture."""
    return DatabaseManager("sqlite:///:memory:")


def test_log_parser_parse_standard_log(sample_config):
    """Test parsing standard log format."""
    parser = LogParser(sample_config["parsing"])
    log_content = "2024-01-01 10:00:00 ERROR: Database connection failed"
    
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value = [log_content]
        errors = parser._parse_standard_line(log_content)
    
    assert errors is not None
    assert "error_message" in errors


def test_error_categorizer_categorize_database_error(sample_config):
    """Test categorizing database error."""
    categorizer = ErrorCategorizer(sample_config["categorization"])
    result = categorizer.categorize_error(
        "Database connection timeout",
        error_type="ConnectionError",
    )
    assert result["category"] == "database"
    assert result["severity"] == "high"


def test_error_categorizer_categorize_auth_error(sample_config):
    """Test categorizing authentication error."""
    categorizer = ErrorCategorizer(sample_config["categorization"])
    result = categorizer.categorize_error(
        "Unauthorized access attempt",
        error_type="AuthenticationError",
    )
    assert result["category"] == "authentication"


def test_pattern_identifier_create_signature(sample_config):
    """Test creating error signature."""
    identifier = PatternIdentifier(sample_config["pattern_identification"])
    error = {
        "error_message": "Database connection failed",
        "error_type": "ConnectionError",
    }
    signature = identifier._create_error_signature(error)
    assert signature is not None
    assert len(signature) > 0


def test_pattern_identifier_identify_patterns(sample_config):
    """Test identifying error patterns."""
    identifier = PatternIdentifier(sample_config["pattern_identification"])
    errors = [
        {
            "error_message": "Database connection failed",
            "error_type": "ConnectionError",
            "timestamp": datetime.utcnow(),
        }
        for _ in range(5)
    ]
    patterns = identifier.identify_patterns(errors)
    assert len(patterns) > 0


def test_error_monitor_calculate_error_rate(db_manager, sample_config):
    """Test calculating error rate."""
    db_manager.create_tables()
    monitor = ErrorMonitor(db_manager, sample_config["monitoring"])
    
    for _ in range(10):
        db_manager.add_error_log(
            error_message="Test error",
            application="test_app",
            environment="test",
        )
    
    error_rate = monitor.calculate_error_rate("test_app", "test", hours=1)
    assert "error_count" in error_rate
    assert "error_rate" in error_rate


def test_bug_report_generator_generate_title(sample_config):
    """Test generating bug report title."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    generator = BugReportGenerator(db_manager, sample_config["bug_reports"])
    
    pattern = {
        "error_type": "ConnectionError",
        "frequency": 10,
        "trend": "increasing",
    }
    errors = [{"id": i} for i in range(10)]
    
    title = generator._generate_title(pattern, errors)
    assert "ConnectionError" in title
    assert "10" in title


def test_bug_report_generator_determine_priority(sample_config):
    """Test determining bug report priority."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    generator = BugReportGenerator(db_manager, sample_config["bug_reports"])
    
    pattern = {"frequency": 100, "trend": "increasing"}
    errors = [{"id": i} for i in range(100)]
    
    priority = generator._determine_priority(pattern, errors, error_rate=15.0)
    assert priority in ["low", "medium", "high", "urgent"]


def test_database_manager_add_error_log(db_manager):
    """Test adding error log."""
    db_manager.create_tables()
    error_log = db_manager.add_error_log(
        error_message="Test error",
        error_type="TestError",
        application="test_app",
    )
    assert error_log.id is not None
    assert error_log.error_message == "Test error"


def test_database_manager_add_error_category(db_manager):
    """Test adding error category."""
    db_manager.create_tables()
    category = db_manager.add_error_category(
        "test_category",
        "Test category description",
    )
    assert category.id is not None
    assert category.name == "test_category"


def test_database_manager_create_bug_report(db_manager):
    """Test creating bug report."""
    db_manager.create_tables()
    bug_report = db_manager.create_bug_report(
        title="Test Bug",
        description="Test description",
        priority="high",
        severity="medium",
    )
    assert bug_report.id is not None
    assert bug_report.title == "Test Bug"
    assert bug_report.priority == "high"


def test_database_manager_get_recent_errors(db_manager):
    """Test getting recent errors."""
    db_manager.create_tables()
    db_manager.add_error_log(error_message="Error 1")
    db_manager.add_error_log(error_message="Error 2")
    
    recent = db_manager.get_recent_errors(limit=10)
    assert len(recent) == 2


def test_pattern_identifier_calculate_trend(sample_config):
    """Test calculating error trend."""
    identifier = PatternIdentifier(sample_config["pattern_identification"])
    
    timestamps = [
        datetime(2024, 1, 1, 10, 0, 0),
        datetime(2024, 1, 1, 11, 0, 0),
        datetime(2024, 1, 1, 12, 0, 0),
        datetime(2024, 1, 1, 13, 0, 0),
        datetime(2024, 1, 1, 14, 0, 0),
    ]
    
    trend = identifier._calculate_trend(timestamps)
    assert trend in ["increasing", "decreasing", "stable"]
