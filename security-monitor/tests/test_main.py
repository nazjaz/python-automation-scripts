"""Unit tests for security monitoring system."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Application, SecurityScan, Vulnerability
from src.scan_monitor import ScanMonitor
from src.vulnerability_tracker import VulnerabilityTracker
from src.fix_prioritizer import FixPrioritizer
from src.compliance_reporter import ComplianceReporter
from src.remediation_timeline import RemediationTimeline


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "scan_monitoring": {
            "monitoring_enabled": True,
        },
        "vulnerability_tracking": {
            "tracking_enabled": True,
        },
        "fix_prioritization": {
            "severity_weights": {
                "critical": 10.0,
                "high": 7.0,
                "medium": 4.0,
                "low": 1.0,
            },
        },
        "compliance": {
            "compliance_thresholds": {
                "critical": 0,
                "high": 5,
                "medium": 20,
            },
        },
        "remediation": {
            "timeline_parameters": {
                "critical": {"days": 1},
                "high": {"days": 7},
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


def test_scan_monitor_monitor_scan(db_manager, sample_config):
    """Test monitoring scan."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    scan = db_manager.add_security_scan(
        "scan1", application.id, "static", datetime.utcnow()
    )
    
    monitor = ScanMonitor(db_manager, sample_config["scan_monitoring"])
    result = monitor.monitor_scan("scan1")
    
    assert result["scan_id"] == "scan1"
    assert "status" in result


def test_vulnerability_tracker_track(db_manager, sample_config):
    """Test tracking vulnerability."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    vulnerability = db_manager.add_vulnerability(
        "vuln1", application.id, "Test Vulnerability", "high", cvss_score=7.5
    )
    
    tracker = VulnerabilityTracker(db_manager, sample_config["vulnerability_tracking"])
    result = tracker.track_vulnerability("vuln1")
    
    assert result["vulnerability_id"] == "vuln1"
    assert result["severity"] == "high"


def test_fix_prioritizer_prioritize(db_manager, sample_config):
    """Test prioritizing fix."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    vulnerability = db_manager.add_vulnerability(
        "vuln1", application.id, "Test Vulnerability", "critical", cvss_score=9.5
    )
    
    prioritizer = FixPrioritizer(db_manager, sample_config["fix_prioritization"])
    result = prioritizer.prioritize_fix("vuln1")
    
    assert "priority_level" in result
    assert "priority_score" in result


def test_compliance_reporter_generate(db_manager, sample_config):
    """Test generating compliance report."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    
    reporter = ComplianceReporter(db_manager, sample_config["compliance"])
    result = reporter.generate_compliance_report(application.id)
    
    assert "compliance_status" in result
    assert "compliance_score" in result


def test_remediation_timeline_generate(db_manager, sample_config):
    """Test generating remediation timeline."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    vulnerability = db_manager.add_vulnerability(
        "vuln1", application.id, "Test Vulnerability", "high"
    )
    
    timeline_gen = RemediationTimeline(db_manager, sample_config["remediation"])
    result = timeline_gen.generate_timeline("vuln1")
    
    assert "target_fix_date" in result
    assert "remediation_steps" in result


def test_database_manager_add_application(db_manager):
    """Test adding application."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App", version="1.0")
    
    assert application.id is not None
    assert application.application_id == "app1"


def test_database_manager_add_security_scan(db_manager):
    """Test adding security scan."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    scan = db_manager.add_security_scan(
        "scan1", application.id, "static", datetime.utcnow()
    )
    
    assert scan.id is not None
    assert scan.scan_id == "scan1"


def test_database_manager_add_vulnerability(db_manager):
    """Test adding vulnerability."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    vulnerability = db_manager.add_vulnerability(
        "vuln1", application.id, "Test Vulnerability", "high", cvss_score=7.5
    )
    
    assert vulnerability.id is not None
    assert vulnerability.vulnerability_id == "vuln1"


def test_database_manager_add_fix(db_manager):
    """Test adding fix."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    vulnerability = db_manager.add_vulnerability(
        "vuln1", application.id, "Test Vulnerability", "high"
    )
    
    fix = db_manager.add_fix(
        vulnerability.id, "patch", "Apply security patch", "high", estimated_effort_hours=8.0
    )
    
    assert fix.id is not None
    assert fix.priority == "high"


def test_vulnerability_tracker_get_statistics(db_manager, sample_config):
    """Test getting vulnerability statistics."""
    db_manager.create_tables()
    application = db_manager.add_application("app1", "Test App")
    db_manager.add_vulnerability("vuln1", application.id, "Test", "high")
    
    tracker = VulnerabilityTracker(db_manager, sample_config["vulnerability_tracking"])
    stats = tracker.get_vulnerability_statistics(application.id)
    
    assert "total_vulnerabilities" in stats
