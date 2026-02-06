"""Unit tests for data pipeline monitoring system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Pipeline, PipelineRun, Failure, QualityCheck
from src.pipeline_monitor import PipelineMonitor
from src.failure_detector import FailureDetector
from src.data_quality_checker import DataQualityChecker
from src.remediation_workflow import RemediationWorkflow
from src.alerting import Alerting


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "monitoring": {
            "health_check_interval_minutes": 5,
            "degraded_threshold": 0.8,
            "unhealthy_threshold": 0.5,
        },
        "failure_detection": {
            "failure_patterns": {
                "timeout": ["timeout", "timed out"],
                "connection": ["connection error"],
            },
            "severity_rules": {
                "failure_types": {
                    "timeout": "high",
                    "connection": "high",
                },
            },
        },
        "quality_checks": {
            "quality_checks": {
                "completeness": {
                    "type": "completeness",
                    "threshold": 0.95,
                    "required_fields": ["id", "timestamp"],
                },
            },
            "thresholds": {
                "critical": 0.5,
                "high": 0.7,
            },
        },
        "remediation": {
            "workflow_templates": {
                "timeout": {
                    "name": "Timeout Remediation",
                    "type": "retry",
                    "steps": [{"type": "retry", "action": "retry_pipeline"}],
                },
                "default": {
                    "name": "Default Remediation",
                    "type": "generic",
                    "steps": [],
                },
            },
        },
        "alerting": {
            "alert_channels": {
                "critical": [{"type": "email", "enabled": True}],
            },
            "email_enabled": False,
            "alert_rules": {
                "min_severity": "medium",
            },
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


def test_pipeline_monitor_check_health(db_manager, sample_config):
    """Test checking pipeline health."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline", "Test description")
    
    start_time = datetime.utcnow() - timedelta(minutes=10)
    end_time = datetime.utcnow() - timedelta(minutes=5)
    
    db_manager.add_pipeline_run(
        pipeline.id, "run1", "success", start_time, end_time, records_processed=100
    )
    db_manager.add_pipeline_run(
        pipeline.id, "run2", "failed", start_time, end_time, error_message="Test error"
    )
    
    monitor = PipelineMonitor(db_manager, sample_config["monitoring"])
    health = monitor.check_pipeline_health(pipeline.id)
    
    assert health["health_status"] in ["healthy", "degraded", "unhealthy"]
    assert "success_rate" in health


def test_failure_detector_detect_failures(db_manager, sample_config):
    """Test detecting failures."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    start_time = datetime.utcnow() - timedelta(minutes=10)
    end_time = datetime.utcnow() - timedelta(minutes=5)
    
    db_manager.add_pipeline_run(
        pipeline.id,
        "run1",
        "failed",
        start_time,
        end_time,
        error_message="Connection timeout occurred",
    )
    
    detector = FailureDetector(db_manager, sample_config["failure_detection"])
    failures = detector.detect_failures(pipeline.id)
    
    assert len(failures) > 0
    assert failures[0]["failure_type"] == "timeout"


def test_data_quality_checker_run_checks(db_manager, sample_config):
    """Test running quality checks."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    checker = DataQualityChecker(db_manager, sample_config["quality_checks"])
    data_sample = {"id": "123", "timestamp": "2024-01-01", "value": 100}
    
    results = checker.run_quality_checks(pipeline.id, data_sample)
    
    assert len(results) > 0
    assert all("status" in result for result in results)


def test_remediation_workflow_trigger(db_manager, sample_config):
    """Test triggering remediation workflow."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    remediation = RemediationWorkflow(db_manager, sample_config["remediation"])
    result = remediation.trigger_remediation(pipeline.id, failure_type="timeout")
    
    assert "success" in result
    assert "workflow_id" in result


def test_alerting_send_alert(db_manager, sample_config):
    """Test sending alert."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    alerting = Alerting(db_manager, sample_config["alerting"])
    alert = alerting.send_alert(
        pipeline.id, "failure", "high", "Test Alert", "Test message"
    )
    
    assert alert is not None
    assert alert["severity"] == "high"
    assert alert["alert_type"] == "failure"


def test_database_manager_add_pipeline(db_manager):
    """Test adding pipeline."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline", "Test description")
    
    assert pipeline.id is not None
    assert pipeline.name == "Test Pipeline"


def test_database_manager_add_pipeline_run(db_manager):
    """Test adding pipeline run."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=5)
    
    run = db_manager.add_pipeline_run(
        pipeline.id, "run1", "success", start_time, end_time, records_processed=100
    )
    
    assert run.id is not None
    assert run.status == "success"
    assert run.records_processed == 100


def test_database_manager_add_failure(db_manager):
    """Test adding failure."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    failure = db_manager.add_failure(
        pipeline.id, "timeout", "high", "Connection timeout"
    )
    
    assert failure.id is not None
    assert failure.failure_type == "timeout"
    assert failure.severity == "high"


def test_database_manager_add_quality_check(db_manager):
    """Test adding quality check."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    check = db_manager.add_quality_check(
        pipeline.id,
        "Completeness Check",
        "completeness",
        "passed",
        severity="low",
        result_value=0.98,
        threshold_value=0.95,
    )
    
    assert check.id is not None
    assert check.status == "passed"
    assert check.result_value == 0.98


def test_pipeline_monitor_get_metrics(db_manager, sample_config):
    """Test getting pipeline metrics."""
    db_manager.create_tables()
    pipeline = db_manager.add_pipeline("Test Pipeline")
    
    monitor = PipelineMonitor(db_manager, sample_config["monitoring"])
    metrics = monitor.get_pipeline_metrics(pipeline.id, hours=24)
    
    assert "total_runs" in metrics
    assert "success_rate" in metrics
