"""Application security monitoring automation system.

Monitors application security scans, tracks vulnerabilities, prioritizes fixes,
and generates security compliance reports with remediation timelines.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.scan_monitor import ScanMonitor
from src.vulnerability_tracker import VulnerabilityTracker
from src.fix_prioritizer import FixPrioritizer
from src.compliance_reporter import ComplianceReporter
from src.remediation_timeline import RemediationTimeline
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/security_monitor.log"))
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


def monitor_scan(
    config: dict,
    settings: object,
    scan_id: str,
) -> dict:
    """Monitor security scan.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        scan_id: Scan identifier.

    Returns:
        Dictionary with scan monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = ScanMonitor(db_manager, config.get("scan_monitoring", {}))

    logger.info(f"Monitoring security scan: {scan_id}")

    result = monitor.monitor_scan(scan_id)

    logger.info(f"Scan status: {result.get('status', 'unknown')}")

    return result


def process_scan_results(
    config: dict,
    settings: object,
    scan_id: str,
    vulnerabilities_file: Path,
) -> dict:
    """Process scan results from file.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        scan_id: Scan identifier.
        vulnerabilities_file: Path to vulnerabilities JSON file.

    Returns:
        Dictionary with processing results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = ScanMonitor(db_manager, config.get("scan_monitoring", {}))

    logger.info(f"Processing scan results: {scan_id}")

    with open(vulnerabilities_file, "r") as f:
        vulnerabilities = json.load(f)

    result = monitor.process_scan_results(scan_id, vulnerabilities)

    logger.info(f"Processed {result.get('vulnerabilities_created', 0)} vulnerabilities")

    return result


def track_vulnerability(
    config: dict,
    settings: object,
    vulnerability_id: str,
) -> dict:
    """Track vulnerability.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        vulnerability_id: Vulnerability identifier.

    Returns:
        Dictionary with tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = VulnerabilityTracker(db_manager, config.get("vulnerability_tracking", {}))

    logger.info(f"Tracking vulnerability: {vulnerability_id}")

    result = tracker.track_vulnerability(vulnerability_id)

    return result


def prioritize_fix(
    config: dict,
    settings: object,
    vulnerability_id: str,
) -> dict:
    """Prioritize fix for vulnerability.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        vulnerability_id: Vulnerability identifier.

    Returns:
        Dictionary with prioritization results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    prioritizer = FixPrioritizer(db_manager, config.get("fix_prioritization", {}))

    logger.info(f"Prioritizing fix for vulnerability: {vulnerability_id}")

    result = prioritizer.prioritize_fix(vulnerability_id)

    logger.info(f"Priority level: {result.get('priority_level', 'unknown')}")

    return result


def generate_compliance_report(
    config: dict,
    settings: object,
    application_id: str,
    report_type: str = "security",
) -> dict:
    """Generate compliance report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        application_id: Application identifier.
        report_type: Report type.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    reporter = ComplianceReporter(db_manager, config.get("compliance", {}))

    application = db_manager.get_application(application_id)
    if not application:
        logger.warning(f"Application not found: {application_id}")
        return {"error": "Application not found"}

    logger.info(f"Generating compliance report for application: {application_id}")

    result = reporter.generate_compliance_report(application.id, report_type=report_type)

    logger.info(f"Compliance status: {result.get('compliance_status', 'unknown')}")

    return result


def generate_timeline(
    config: dict,
    settings: object,
    vulnerability_id: str,
) -> dict:
    """Generate remediation timeline.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        vulnerability_id: Vulnerability identifier.

    Returns:
        Dictionary with timeline generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    timeline_gen = RemediationTimeline(db_manager, config.get("remediation", {}))

    logger.info(f"Generating remediation timeline for vulnerability: {vulnerability_id}")

    result = timeline_gen.generate_timeline(vulnerability_id)

    logger.info(f"Target fix date: {result.get('target_fix_date', 'N/A')}")

    return result


def generate_reports(
    config: dict,
    settings: object,
    application_id: Optional[str] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        application_id: Optional application ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating security monitoring reports", extra={"application_id": application_id})

    reports = report_generator.generate_reports(application_id=application_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "application_id": application_id,
    }


def main() -> None:
    """Main entry point for security monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Application security monitoring automation system"
    )
    parser.add_argument(
        "--monitor-scan",
        metavar="SCAN_ID",
        help="Monitor security scan",
    )
    parser.add_argument(
        "--process-results",
        nargs=2,
        metavar=("SCAN_ID", "FILE"),
        help="Process scan results from JSON file",
    )
    parser.add_argument(
        "--track",
        metavar="VULNERABILITY_ID",
        help="Track vulnerability",
    )
    parser.add_argument(
        "--prioritize",
        metavar="VULNERABILITY_ID",
        help="Prioritize fix for vulnerability",
    )
    parser.add_argument(
        "--generate-compliance",
        metavar="APPLICATION_ID",
        help="Generate compliance report",
    )
    parser.add_argument(
        "--generate-timeline",
        metavar="VULNERABILITY_ID",
        help="Generate remediation timeline",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--application-id",
        help="Filter by application ID",
    )
    parser.add_argument(
        "--report-type",
        default="security",
        help="Report type (default: security)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.monitor_scan,
        args.process_results,
        args.track,
        args.prioritize,
        args.generate_compliance,
        args.generate_timeline,
        args.report,
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
        if args.monitor_scan:
            result = monitor_scan(
                config=config,
                settings=settings,
                scan_id=args.monitor_scan,
            )
            print(f"\nScan monitoring:")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Vulnerabilities found: {result.get('vulnerabilities_found', 0)}")
            print(f"Critical: {result.get('critical_count', 0)}")

        if args.process_results:
            scan_id, file_path = args.process_results
            result = process_scan_results(
                config=config,
                settings=settings,
                scan_id=scan_id,
                vulnerabilities_file=Path(file_path),
            )
            if result.get("success"):
                print(f"\nScan results processed:")
                print(f"Vulnerabilities created: {result.get('vulnerabilities_created', 0)}")
                print(f"Critical: {result.get('critical_count', 0)}")
                print(f"High: {result.get('high_count', 0)}")

        if args.track:
            result = track_vulnerability(
                config=config,
                settings=settings,
                vulnerability_id=args.track,
            )
            print(f"\nVulnerability tracking:")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"Severity: {result.get('severity', 'unknown')}")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Days open: {result.get('days_open', 'N/A')}")

        if args.prioritize:
            result = prioritize_fix(
                config=config,
                settings=settings,
                vulnerability_id=args.prioritize,
            )
            print(f"\nFix prioritization:")
            print(f"Priority level: {result.get('priority_level', 'unknown')}")
            print(f"Priority score: {result.get('priority_score', 0):.1f}")
            print(f"Estimated effort: {result.get('estimated_effort_hours', 0):.1f} hours")

        if args.generate_compliance:
            result = generate_compliance_report(
                config=config,
                settings=settings,
                application_id=args.generate_compliance,
                report_type=args.report_type,
            )
            if result.get("compliance_status"):
                print(f"\nCompliance report generated:")
                print(f"Compliance status: {result['compliance_status']}")
                print(f"Compliance score: {result.get('compliance_score', 0):.1f}")
                print(f"Total vulnerabilities: {result.get('total_vulnerabilities', 0)}")

        if args.generate_timeline:
            result = generate_timeline(
                config=config,
                settings=settings,
                vulnerability_id=args.generate_timeline,
            )
            if result.get("target_fix_date"):
                print(f"\nRemediation timeline generated:")
                print(f"Target fix date: {result['target_fix_date']}")
                print(f"Days until target: {result.get('days_until_target', 0)}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                application_id=args.application_id,
            )
            print(f"\nReports generated:")
            for report_type, path in result["reports"].items():
                print(f"  {report_type.upper()}: {path}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
