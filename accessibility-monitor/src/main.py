"""Accessibility monitoring automation system.

Monitors website accessibility compliance, identifies WCAG violations,
generates remediation reports, and tracks improvement progress over time.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.accessibility_scanner import AccessibilityScanner
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.progress_tracker import ProgressTracker
from src.remediation_generator import RemediationGenerator
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/accessibility_monitor.log"))
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


def add_website(
    config: dict,
    settings: object,
    url: str,
    name: Optional[str] = None,
) -> dict:
    """Add a website to monitor.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        url: Website URL.
        name: Optional website name.

    Returns:
        Dictionary with website information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    website = db_manager.add_website(url=url, name=name)

    logger.info(f"Added website: {website.url}", extra={"website_id": website.id, "url": url})

    return {
        "success": True,
        "website_id": website.id,
        "url": website.url,
        "name": website.name,
    }


def scan_website(
    config: dict,
    settings: object,
    website_id: int,
    start_url: Optional[str] = None,
    max_pages: Optional[int] = None,
) -> dict:
    """Scan website for accessibility issues.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.
        start_url: Optional starting URL (defaults to website URL).
        max_pages: Optional maximum pages to scan.

    Returns:
        Dictionary with scan results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    scanner = AccessibilityScanner(db_manager, config)

    from src.database import Website
    session = db_manager.get_session()
    try:
        website = session.query(Website).filter_by(id=website_id).first()
        if not website:
            return {"success": False, "error": f"Website {website_id} not found"}
        start_url = start_url or website.url
    finally:
        session.close()

    logger.info("Scanning website", extra={"website_id": website_id, "start_url": start_url})

    scans = scanner.scan_website(
        website_id=website_id,
        start_url=start_url,
        max_pages=max_pages,
    )

    logger.info(
        f"Scan completed: {len(scans)} pages scanned",
        extra={"pages_scanned": len(scans), "website_id": website_id},
    )

    return {
        "success": True,
        "pages_scanned": len(scans),
        "scan_ids": [s.id for s in scans],
    }


def generate_remediation_tasks(
    config: dict,
    settings: object,
    website_id: Optional[int] = None,
    scan_id: Optional[int] = None,
    severity: Optional[str] = None,
) -> dict:
    """Generate remediation tasks from violations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Optional website ID filter.
        scan_id: Optional scan ID filter.
        severity: Optional severity filter.

    Returns:
        Dictionary with task generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = RemediationGenerator(db_manager, config)

    logger.info("Generating remediation tasks", extra={"website_id": website_id, "scan_id": scan_id})

    tasks = generator.generate_remediation_tasks(
        website_id=website_id,
        scan_id=scan_id,
        severity=severity,
    )

    logger.info(
        f"Generated {len(tasks)} remediation tasks",
        extra={"task_count": len(tasks)},
    )

    return {
        "success": True,
        "task_count": len(tasks),
        "task_ids": [t.id for t in tasks],
    }


def track_progress(
    config: dict,
    settings: object,
    website_id: int,
    days: int = 30,
) -> dict:
    """Track accessibility improvement progress.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.
        days: Number of days to analyze.

    Returns:
        Dictionary with progress tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ProgressTracker(db_manager, config)

    logger.info("Tracking progress", extra={"website_id": website_id, "days": days})

    trend = tracker.get_progress_trend(website_id, days=days)
    summary = tracker.get_improvement_summary(website_id, days=days)

    logger.info(
        f"Progress tracking completed",
        extra={"trend": trend.get("trend"), "website_id": website_id},
    )

    return {
        "success": True,
        "trend": trend,
        "summary": summary,
    }


def generate_report(
    config: dict,
    settings: object,
    website_id: Optional[int] = None,
    scan_id: Optional[int] = None,
    format: str = "html",
) -> dict:
    """Generate accessibility compliance report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Optional website ID filter.
        scan_id: Optional scan ID filter.
        format: Report format (html, csv, json).

    Returns:
        Dictionary with report path.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = ReportGenerator(
        db_manager,
        config,
        output_dir=config.get("reporting", {}).get("output_directory", "reports"),
    )

    logger.info("Generating accessibility report", extra={"format": format, "website_id": website_id, "scan_id": scan_id})

    if format == "html":
        report_path = generator.generate_html_report(
            website_id=website_id,
            scan_id=scan_id,
        )
    elif format == "csv":
        report_path = generator.generate_csv_report(
            website_id=website_id,
            scan_id=scan_id,
        )
    else:
        return {"success": False, "error": f"Unsupported format: {format}"}

    logger.info(
        f"Report generated: {report_path}",
        extra={"report_path": str(report_path)},
    )

    return {
        "success": True,
        "report_path": str(report_path),
        "format": format,
    }


def main() -> None:
    """Main entry point for accessibility monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Accessibility monitoring automation system"
    )
    parser.add_argument(
        "--add-website",
        action="store_true",
        help="Add a website to monitor",
    )
    parser.add_argument(
        "--url", help="Website URL"
    )
    parser.add_argument(
        "--name", help="Website name"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan website for accessibility issues",
    )
    parser.add_argument(
        "--website-id", type=int, help="Website ID"
    )
    parser.add_argument(
        "--start-url", help="Starting URL for scan"
    )
    parser.add_argument(
        "--max-pages", type=int, help="Maximum pages to scan"
    )
    parser.add_argument(
        "--generate-tasks",
        action="store_true",
        help="Generate remediation tasks",
    )
    parser.add_argument(
        "--scan-id", type=int, help="Scan ID"
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        help="Filter by severity",
    )
    parser.add_argument(
        "--track-progress",
        action="store_true",
        help="Track accessibility improvement progress",
    )
    parser.add_argument(
        "--progress-days", type=int, default=30, help="Days to analyze for progress (default: 30)"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate accessibility compliance report",
    )
    parser.add_argument(
        "--format",
        choices=["html", "csv"],
        default="html",
        help="Report format (default: html)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.add_website,
        args.scan,
        args.generate_tasks,
        args.track_progress,
        args.generate_report,
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
        if args.add_website:
            if not args.url:
                print("Error: --url is required for --add-website", file=sys.stderr)
                sys.exit(1)

            result = add_website(
                config=config,
                settings=settings,
                url=args.url,
                name=args.name,
            )

            print(f"\nWebsite added successfully:")
            print(f"ID: {result['website_id']}")
            print(f"URL: {result['url']}")
            print(f"Name: {result['name']}")

        elif args.scan:
            if not args.website_id:
                print("Error: --website-id is required for --scan", file=sys.stderr)
                sys.exit(1)

            result = scan_website(
                config=config,
                settings=settings,
                website_id=args.website_id,
                start_url=args.start_url,
                max_pages=args.max_pages,
            )

            if result["success"]:
                print(f"\nScan completed:")
                print(f"Pages scanned: {result['pages_scanned']}")
                print(f"Scan IDs: {', '.join(map(str, result['scan_ids']))}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.generate_tasks:
            result = generate_remediation_tasks(
                config=config,
                settings=settings,
                website_id=args.website_id,
                scan_id=args.scan_id,
                severity=args.severity,
            )

            print(f"\nRemediation tasks generated:")
            print(f"Tasks created: {result['task_count']}")

        elif args.track_progress:
            if not args.website_id:
                print("Error: --website-id is required for --track-progress", file=sys.stderr)
                sys.exit(1)

            result = track_progress(
                config=config,
                settings=settings,
                website_id=args.website_id,
                days=args.progress_days,
            )

            print(f"\nProgress tracking:")
            print(f"Trend: {result['trend'].get('trend', 'unknown')}")
            if result.get("summary"):
                summary = result["summary"]
                print(f"Current Score: {summary.get('current_score', 'N/A')}")
                print(f"Violation Reduction: {summary.get('violation_reduction', 0)}")

        elif args.generate_report:
            result = generate_report(
                config=config,
                settings=settings,
                website_id=args.website_id,
                scan_id=args.scan_id,
                format=args.format,
            )

            if result["success"]:
                print(f"\nReport generated:")
                print(f"Format: {result['format'].upper()}")
                print(f"Path: {result['report_path']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
