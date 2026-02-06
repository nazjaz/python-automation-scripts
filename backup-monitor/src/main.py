"""Backup monitoring automation system.

Monitors system backups, verifies backup integrity, tests restore procedures,
and generates backup health reports with failure alerts.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.alert_system import AlertSystem
from src.backup_monitor import BackupMonitor
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.health_reporter import HealthReporter
from src.integrity_verifier import IntegrityVerifier
from src.restore_tester import RestoreTester


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/backup_monitor.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=log_config.get("max_bytes", 10485760),
        backupCount=log_config.get("backup_count", 5),
    )

    formatter = logging.Formatter(log_config.get("format"))
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def monitor_backups(
    config: dict,
    settings: object,
    location_name: Optional[str] = None,
) -> dict:
    """Monitor backup locations and track backups.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        location_name: Optional location name filter.

    Returns:
        Dictionary with monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    backup_config = config.get("backups", {})
    locations_config = backup_config.get("locations", [])

    for loc_config in locations_config:
        db_manager.add_backup_location(
            name=loc_config["name"],
            path=loc_config["path"],
            backup_type=loc_config["type"],
            schedule=loc_config.get("schedule"),
            retention_days=loc_config.get("retention_days", 30),
            verify_integrity=loc_config.get("verify_integrity", True),
            test_restore=loc_config.get("test_restore", False),
        )

    monitor = BackupMonitor(db_manager, config)

    if location_name:
        locations = [
            l for l in db_manager.get_backup_locations()
            if l.name == location_name
        ]
        if not locations:
            logger.error(f"Location not found: {location_name}")
            return {"success": False, "error": f"Location not found: {location_name}"}
        all_backups = {}
        for location in locations:
            backups = monitor.scan_backup_location(location)
            all_backups[location.name] = backups
    else:
        all_backups = monitor.monitor_all_locations()

    total_backups = sum(len(backups) for backups in all_backups.values())

    logger.info(
        f"Backup monitoring completed: {total_backups} backups found",
        extra={"total_backups": total_backups},
    )

    return {
        "success": True,
        "total_backups": total_backups,
        "locations": {k: len(v) for k, v in all_backups.items()},
    }


def verify_backups(
    config: dict,
    settings: object,
    location_id: Optional[int] = None,
    days: Optional[int] = None,
) -> dict:
    """Verify backup integrity.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        location_id: Optional location ID filter.
        days: Optional number of days to look back.

    Returns:
        Dictionary with verification results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    verifier = IntegrityVerifier(db_manager, config)

    logger.info("Starting backup verification", extra={"location_id": location_id, "days": days})

    all_verifications = verifier.verify_all_backups(
        location_id=location_id, days=days
    )

    total_verifications = sum(len(v) for v in all_verifications.values())
    passed = sum(
        len([v for v in verifications if v.status == "passed"])
        for verifications in all_verifications.values()
    )

    logger.info(
        f"Backup verification completed: {passed}/{total_verifications} passed",
        extra={"total": total_verifications, "passed": passed},
    )

    return {
        "success": True,
        "total_verifications": total_verifications,
        "passed": passed,
        "failed": total_verifications - passed,
    }


def test_restores(
    config: dict,
    settings: object,
    location_id: Optional[int] = None,
    days: Optional[int] = None,
) -> dict:
    """Test restore procedures.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        location_id: Optional location ID filter.
        days: Optional number of days to look back.

    Returns:
        Dictionary with restore test results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tester = RestoreTester(db_manager, config)

    logger.info("Starting restore tests", extra={"location_id": location_id, "days": days})

    restore_config = config.get("backups", {}).get("restore_testing", {})
    test_frequency_days = restore_config.get("test_frequency_days", 7)

    if days is None:
        days = test_frequency_days

    all_tests = tester.test_all_backups(
        location_id=location_id, days=days, limit=10
    )

    passed = len([t for t in all_tests if t.status == "passed"])
    failed = len([t for t in all_tests if t.status == "failed"])

    logger.info(
        f"Restore tests completed: {passed}/{len(all_tests)} passed",
        extra={"total": len(all_tests), "passed": passed, "failed": failed},
    )

    return {
        "success": True,
        "total_tests": len(all_tests),
        "passed": passed,
        "failed": failed,
    }


def generate_health_report(
    config: dict,
    settings: object,
    location_id: Optional[int] = None,
    days: int = 7,
) -> dict:
    """Generate backup health report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        location_id: Optional location ID filter.
        days: Number of days to analyze.

    Returns:
        Dictionary with report paths.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    reporter = HealthReporter(
        db_manager,
        output_dir=config.get("reporting", {}).get("output_directory", "reports"),
    )

    logger.info("Generating health report", extra={"location_id": location_id, "days": days})

    reports = {}

    if config.get("reporting", {}).get("generate_html", True):
        reports["html"] = str(
            reporter.generate_html_report(location_id=location_id, days=days)
        )

    if config.get("reporting", {}).get("generate_csv", True):
        reports["csv"] = str(
            reporter.generate_csv_report(location_id=location_id, days=days)
        )

    logger.info(
        f"Health report generated: {len(reports)} report(s)",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": reports,
    }


def check_alerts(
    config: dict,
    settings: object,
    location_id: Optional[int] = None,
) -> dict:
    """Check for failures and send alerts.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        location_id: Optional location ID filter.

    Returns:
        Dictionary with alert results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    alert_system = AlertSystem(db_manager, config)

    logger.info("Checking for failures and sending alerts", extra={"location_id": location_id})

    backup_alerts = alert_system.check_and_alert_failures(
        location_id=location_id, days=1
    )
    verification_alerts = alert_system.check_and_alert_verification_failures(
        location_id=location_id, days=1
    )
    restore_alerts = alert_system.check_and_alert_restore_failures(
        location_id=location_id, days=7
    )

    total_alerts = len(backup_alerts) + len(verification_alerts) + len(restore_alerts)

    logger.info(
        f"Alert check completed: {total_alerts} alert(s) sent",
        extra={"total_alerts": total_alerts},
    )

    return {
        "success": True,
        "backup_alerts": len(backup_alerts),
        "verification_alerts": len(verification_alerts),
        "restore_alerts": len(restore_alerts),
        "total_alerts": total_alerts,
    }


def main() -> None:
    """Main entry point for backup monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Backup monitoring automation system"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor backup locations and track backups",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify backup integrity",
    )
    parser.add_argument(
        "--test-restore",
        action="store_true",
        help="Test restore procedures",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate backup health report",
    )
    parser.add_argument(
        "--check-alerts",
        action="store_true",
        help="Check for failures and send alerts",
    )
    parser.add_argument(
        "--location-id",
        type=int,
        help="Filter by location ID",
    )
    parser.add_argument(
        "--location-name",
        help="Filter by location name",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.monitor,
        args.verify,
        args.test_restore,
        args.report,
        args.check_alerts,
    ]):
        parser.print_help()
        sys.exit(1)

    try:
        config = load_config(args.config) if args.config else load_config()
        settings = get_settings()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.get("logging", {}))

    logger = logging.getLogger(__name__)

    try:
        if args.monitor:
            result = monitor_backups(
                config=config,
                settings=settings,
                location_name=args.location_name,
            )
            print(f"\nBackup monitoring completed:")
            print(f"Total backups found: {result['total_backups']}")
            for location, count in result["locations"].items():
                print(f"  {location}: {count} backups")

        if args.verify:
            result = verify_backups(
                config=config,
                settings=settings,
                location_id=args.location_id,
                days=args.days,
            )
            print(f"\nBackup verification completed:")
            print(f"Total verifications: {result['total_verifications']}")
            print(f"Passed: {result['passed']}")
            print(f"Failed: {result['failed']}")

        if args.test_restore:
            result = test_restores(
                config=config,
                settings=settings,
                location_id=args.location_id,
                days=args.days,
            )
            print(f"\nRestore tests completed:")
            print(f"Total tests: {result['total_tests']}")
            print(f"Passed: {result['passed']}")
            print(f"Failed: {result['failed']}")

        if args.report:
            result = generate_health_report(
                config=config,
                settings=settings,
                location_id=args.location_id,
                days=args.days,
            )
            print(f"\nHealth report generated:")
            for report_type, path in result["reports"].items():
                print(f"  {report_type.upper()}: {path}")

        if args.check_alerts:
            result = check_alerts(
                config=config,
                settings=settings,
                location_id=args.location_id,
            )
            print(f"\nAlert check completed:")
            print(f"Total alerts sent: {result['total_alerts']}")
            print(f"  Backup failures: {result['backup_alerts']}")
            print(f"  Verification failures: {result['verification_alerts']}")
            print(f"  Restore failures: {result['restore_alerts']}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
