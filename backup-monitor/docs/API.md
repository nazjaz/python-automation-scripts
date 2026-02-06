# Backup Monitor API Documentation

## Overview

The Backup Monitor provides a comprehensive API for monitoring backups, verifying integrity, testing restore procedures, and generating health reports.

## Architecture

The system is built with a modular architecture:

- **Backup Monitor**: Scans backup locations and tracks backup files
- **Integrity Verifier**: Verifies backup integrity using multiple methods
- **Restore Tester**: Tests restore procedures to ensure recoverability
- **Health Reporter**: Generates health reports with metrics and scores
- **Alert System**: Sends alerts for failures and issues

## Database Schema

### BackupLocation

Stores backup location configurations.

- `id`: Primary key
- `name`: Location name (unique)
- `path`: Backup path
- `backup_type`: Type of backup (database, file, etc.)
- `schedule`: Backup schedule
- `retention_days`: Retention period in days
- `verify_integrity`: Whether to verify integrity
- `test_restore`: Whether to test restore
- `enabled`: Whether location is enabled

### Backup

Stores backup file records.

- `id`: Primary key
- `location_id`: Foreign key to BackupLocation
- `filename`: Backup filename
- `filepath`: Full file path
- `size_bytes`: File size in bytes
- `checksum`: File checksum
- `checksum_algorithm`: Checksum algorithm used
- `backup_timestamp`: When backup was created
- `status`: Backup status (pending, completed, failed)
- `error_message`: Error message if failed

### BackupVerification

Stores verification results.

- `id`: Primary key
- `backup_id`: Foreign key to Backup
- `verification_type`: Type of verification (checksum, size_validation, etc.)
- `status`: Verification status (passed, failed, error, skipped)
- `result`: Verification result text
- `error_message`: Error message if failed
- `verified_at`: When verification was performed

### RestoreTest

Stores restore test results.

- `id`: Primary key
- `backup_id`: Foreign key to Backup
- `test_location`: Test restore location
- `status`: Test status (passed, failed, error)
- `duration_seconds`: Test duration
- `result`: Test result text
- `error_message`: Error message if failed
- `tested_at`: When test was performed

### HealthMetric

Stores health metrics for locations.

- `id`: Primary key
- `location_id`: Foreign key to BackupLocation
- `metric_date`: Metric date
- `total_backups`: Total number of backups
- `successful_backups`: Number of successful backups
- `failed_backups`: Number of failed backups
- `total_size_bytes`: Total backup size
- `verification_success_rate`: Verification success rate
- `restore_test_success_rate`: Restore test success rate
- `health_score`: Overall health score

### Alert

Stores alert records.

- `id`: Primary key
- `location_id`: Optional foreign key to BackupLocation
- `backup_id`: Optional foreign key to Backup
- `alert_type`: Type of alert
- `severity`: Alert severity (critical, warning, info)
- `message`: Alert message
- `resolved`: Whether alert is resolved
- `created_at`: When alert was created

## Usage Examples

### Monitoring Backups

```python
from src.config import load_config, get_settings
from src.database import DatabaseManager
from src.backup_monitor import BackupMonitor

config = load_config()
settings = get_settings()
db_manager = DatabaseManager(settings.database.url)
db_manager.create_tables()

monitor = BackupMonitor(db_manager, config)
all_backups = monitor.monitor_all_locations()
```

### Verifying Backup Integrity

```python
from src.integrity_verifier import IntegrityVerifier

verifier = IntegrityVerifier(db_manager, config)
verifications = verifier.verify_all_backups(location_id=1, days=7)
```

### Testing Restore Procedures

```python
from src.restore_tester import RestoreTester

tester = RestoreTester(db_manager, config)
restore_tests = tester.test_all_backups(location_id=1, days=7)
```

### Generating Health Reports

```python
from src.health_reporter import HealthReporter

reporter = HealthReporter(db_manager, output_dir="reports")
html_path = reporter.generate_html_report(location_id=1, days=7)
csv_path = reporter.generate_csv_report(location_id=1, days=7)
```

### Sending Alerts

```python
from src.alert_system import AlertSystem

alert_system = AlertSystem(db_manager, config)
alert = alert_system.send_alert(
    alert_type="backup_failure",
    severity="critical",
    message="Backup failed: database_backup.tar.gz",
    location_id=1,
    backup_id=123,
)
```

## Verification Methods

### Checksum Verification

Calculates file checksum using specified algorithm (SHA256, MD5, etc.) and compares with stored checksum.

### Size Validation

Verifies backup file size matches the size stored in database.

### Timestamp Validation

Checks backup file modification timestamp matches stored timestamp.

## Restore Testing

### File Backups

- Extracts ZIP, TAR, TAR.GZ archives
- Validates extracted files
- Copies single files to test location

### Database Backups

- Validates SQL file format
- Checks database dump file integrity
- Verifies file size and format

## Health Scoring

Health scores are calculated as:

```
health_score = (backup_success_rate × 0.5) +
               (verification_success_rate × 0.3) +
               (restore_test_success_rate × 0.2)
```

## Alert Types

- `backup_failure`: Backup creation or completion failed
- `verification_failure`: Backup integrity verification failed
- `restore_failure`: Restore test failed
- `health_degradation`: Health score dropped below threshold

## Alert Channels

### Email

Configure SMTP settings in `config.yaml`:

```yaml
alerts:
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    from_email: "backup-monitor@example.com"
    to_emails: ["admin@example.com"]
```

### Slack

Configure webhook URL in `config.yaml`:

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Log

Logs alerts to configured log file (always enabled).

## Extending the System

### Adding New Verification Methods

1. Add method name to `verification.methods` in `config.yaml`
2. Implement method in `IntegrityVerifier` class
3. Add verification logic in `_verify_*` method

### Adding New Backup Types

1. Add backup type handling in `RestoreTester._perform_restore()`
2. Implement restore logic for new type
3. Update configuration documentation

### Custom Alert Channels

1. Add channel configuration to `config.yaml`
2. Implement `_send_*_alert()` method in `AlertSystem`
3. Add channel enable/disable logic
