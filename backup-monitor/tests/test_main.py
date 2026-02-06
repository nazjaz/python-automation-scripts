"""Test suite for backup monitoring system."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    BackupLocation,
    Backup,
    BackupVerification,
    RestoreTest,
)
from src.backup_monitor import BackupMonitor
from src.integrity_verifier import IntegrityVerifier
from src.restore_tester import RestoreTester
from src.alert_system import AlertSystem
from src.health_reporter import HealthReporter


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
        "backups": {
            "locations": [
                {
                    "name": "test_backup",
                    "path": "/tmp/test_backups",
                    "type": "file",
                    "schedule": "daily",
                    "retention_days": 30,
                    "verify_integrity": True,
                    "test_restore": True,
                }
            ],
            "verification": {
                "enabled": True,
                "methods": ["checksum", "size_validation"],
                "checksum_algorithm": "sha256",
            },
            "restore_testing": {
                "enabled": True,
                "test_frequency_days": 7,
                "test_location": "test_backups",
                "cleanup_after_test": True,
            },
        },
        "monitoring": {
            "alert_on_failure": True,
            "alert_on_verification_failure": True,
            "alert_on_restore_failure": True,
        },
        "alerts": {
            "log": {"enabled": True, "level": "ERROR"},
            "email": {"enabled": False},
            "slack": {"enabled": False},
        },
        "reporting": {
            "generate_html": True,
            "generate_csv": True,
            "output_directory": "reports",
        },
    }


@pytest.fixture
def sample_backup_location(test_db):
    """Create sample backup location for testing."""
    location = test_db.add_backup_location(
        name="test_location",
        path="/tmp/test_backups",
        backup_type="file",
        schedule="daily",
    )
    return location


@pytest.fixture
def sample_backup(test_db, sample_backup_location):
    """Create sample backup for testing."""
    backup = test_db.add_backup(
        location_id=sample_backup_location.id,
        filename="test_backup.tar.gz",
        filepath="/tmp/test_backups/test_backup.tar.gz",
        backup_timestamp=datetime.utcnow(),
        size_bytes=1024,
        checksum="abc123",
        checksum_algorithm="sha256",
        status="completed",
    )
    return backup


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            locations = session.query(BackupLocation).all()
            assert len(locations) == 0
        finally:
            session.close()

    def test_add_backup_location(self, test_db):
        """Test adding backup location."""
        location = test_db.add_backup_location(
            name="test_location",
            path="/tmp/backups",
            backup_type="file",
        )
        assert location.id is not None
        assert location.name == "test_location"

    def test_add_backup(self, test_db, sample_backup_location):
        """Test adding backup."""
        backup = test_db.add_backup(
            location_id=sample_backup_location.id,
            filename="backup.tar.gz",
            filepath="/tmp/backup.tar.gz",
            backup_timestamp=datetime.utcnow(),
            size_bytes=2048,
        )
        assert backup.id is not None
        assert backup.filename == "backup.tar.gz"

    def test_add_verification(self, test_db, sample_backup):
        """Test adding verification."""
        verification = test_db.add_verification(
            backup_id=sample_backup.id,
            verification_type="checksum",
            status="passed",
            result="Checksum matches",
        )
        assert verification.id is not None
        assert verification.status == "passed"

    def test_add_restore_test(self, test_db, sample_backup):
        """Test adding restore test."""
        restore_test = test_db.add_restore_test(
            backup_id=sample_backup.id,
            status="passed",
            duration_seconds=10.5,
        )
        assert restore_test.id is not None
        assert restore_test.status == "passed"


class TestBackupMonitor:
    """Test backup monitor functionality."""

    def test_scan_backup_location(self, test_db, sample_config, tmp_path):
        """Test scanning backup location."""
        location = test_db.add_backup_location(
            name="test_scan",
            path=str(tmp_path),
            backup_type="file",
        )

        test_file = tmp_path / "backup.tar.gz"
        test_file.write_bytes(b"test backup data")

        monitor = BackupMonitor(test_db, sample_config)
        backups = monitor.scan_backup_location(location)

        assert len(backups) == 1
        assert backups[0].filename == "backup.tar.gz"

    def test_check_backup_health(self, test_db, sample_config, sample_backup_location):
        """Test backup health check."""
        test_db.add_backup(
            location_id=sample_backup_location.id,
            filename="backup1.tar.gz",
            filepath="/tmp/backup1.tar.gz",
            backup_timestamp=datetime.utcnow(),
            status="completed",
        )

        monitor = BackupMonitor(test_db, sample_config)
        health = monitor.check_backup_health(location_id=sample_backup_location.id, days=7)

        assert sample_backup_location.name in health
        assert health[sample_backup_location.name]["total_backups"] >= 1


class TestIntegrityVerifier:
    """Test integrity verifier functionality."""

    def test_verify_backup(self, test_db, sample_config, sample_backup, tmp_path):
        """Test backup verification."""
        test_file = tmp_path / sample_backup.filename
        test_file.write_bytes(b"test data")
        sample_backup.filepath = str(test_file)

        verifier = IntegrityVerifier(test_db, sample_config)
        verifications = verifier.verify_backup(sample_backup)

        assert len(verifications) > 0
        assert any(v.verification_type == "size_validation" for v in verifications)


class TestRestoreTester:
    """Test restore tester functionality."""

    def test_test_restore(self, test_db, sample_config, sample_backup, tmp_path):
        """Test restore procedure."""
        test_file = tmp_path / sample_backup.filename
        test_file.write_bytes(b"test backup data")
        sample_backup.filepath = str(test_file)

        tester = RestoreTester(test_db, sample_config)
        restore_test = tester.test_restore(sample_backup)

        assert restore_test is not None
        assert restore_test.backup_id == sample_backup.id


class TestAlertSystem:
    """Test alert system functionality."""

    def test_send_alert(self, test_db, sample_config):
        """Test sending alert."""
        alert_system = AlertSystem(test_db, sample_config)
        alert = alert_system.send_alert(
            alert_type="test_alert",
            severity="warning",
            message="Test alert message",
        )

        assert alert.id is not None
        assert alert.alert_type == "test_alert"
        assert alert.severity == "warning"


class TestHealthReporter:
    """Test health reporter functionality."""

    def test_calculate_health_score(self, test_db, sample_backup_location):
        """Test health score calculation."""
        test_db.add_backup(
            location_id=sample_backup_location.id,
            filename="backup.tar.gz",
            filepath="/tmp/backup.tar.gz",
            backup_timestamp=datetime.utcnow(),
            status="completed",
        )

        reporter = HealthReporter(test_db)
        score = reporter.calculate_health_score(sample_backup_location.id, days=7)

        assert 0.0 <= score <= 1.0

    def test_generate_csv_report(self, test_db, sample_backup_location, tmp_path):
        """Test CSV report generation."""
        reporter = HealthReporter(test_db, output_dir=str(tmp_path))
        report_path = reporter.generate_csv_report(
            location_id=sample_backup_location.id, days=7
        )

        assert report_path.exists()
        assert report_path.suffix == ".csv"


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "backups" in config
            assert "monitoring" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
