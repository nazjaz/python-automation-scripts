"""Customer complaint processing automation system.

Processes customer complaints by categorizing issues, routing to appropriate
departments, tracking resolution, and generating customer satisfaction follow-ups.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.complaint_processor import ComplaintProcessor
from src.issue_categorizer import IssueCategorizer
from src.department_router import DepartmentRouter
from src.resolution_tracker import ResolutionTracker
from src.followup_generator import FollowUpGenerator
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/complaint_processor.log"))
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


def process_complaint(
    config: dict,
    settings: object,
    complaint_id: str,
    customer_id: str,
    complaint_text: str,
    customer_name: Optional[str] = None,
    email: Optional[str] = None,
) -> dict:
    """Process a new complaint.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        complaint_id: Complaint identifier.
        customer_id: Customer identifier.
        complaint_text: Complaint text.
        customer_name: Customer name.
        email: Customer email.

    Returns:
        Dictionary with processing results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    processor = ComplaintProcessor(db_manager, config.get("processing", {}))

    logger.info(f"Processing complaint: {complaint_id}")

    result = processor.process_complaint(
        complaint_id=complaint_id,
        customer_id=customer_id,
        complaint_text=complaint_text,
        customer_name=customer_name,
        email=email,
    )

    logger.info(
        f"Complaint processed: category={result.get('category')}, "
        f"department={result.get('department')}"
    )

    return result


def resolve_complaint(
    config: dict,
    settings: object,
    complaint_id: str,
    resolution_text: str,
    resolution_type: str,
    resolved_by: str,
) -> dict:
    """Resolve a complaint.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        complaint_id: Complaint identifier.
        resolution_text: Resolution text.
        resolution_type: Resolution type.
        resolved_by: Person who resolved.

    Returns:
        Dictionary with resolution results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ResolutionTracker(db_manager, config.get("resolution_tracking", {}))

    logger.info(f"Resolving complaint: {complaint_id}")

    result = tracker.add_resolution(
        complaint_id=complaint_id,
        resolution_text=resolution_text,
        resolution_type=resolution_type,
        resolved_by=resolved_by,
    )

    logger.info(f"Complaint resolved: {complaint_id}")

    return result


def generate_followup(
    config: dict,
    settings: object,
    complaint_id: str,
) -> dict:
    """Generate follow-up for complaint.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        complaint_id: Complaint identifier.

    Returns:
        Dictionary with follow-up generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = FollowUpGenerator(db_manager, config.get("followups", {}))

    logger.info(f"Generating follow-up for complaint: {complaint_id}")

    result = generator.generate_followup(complaint_id)

    logger.info(f"Follow-up generated: {result.get('followup_id')}")

    return result


def track_resolution(
    config: dict,
    settings: object,
    complaint_id: str,
) -> dict:
    """Track complaint resolution.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        complaint_id: Complaint identifier.

    Returns:
        Dictionary with resolution tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ResolutionTracker(db_manager, config.get("resolution_tracking", {}))

    logger.info(f"Tracking resolution for complaint: {complaint_id}")

    result = tracker.track_resolution(complaint_id)

    return result


def generate_reports(
    config: dict,
    settings: object,
    complaint_id: Optional[str] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        complaint_id: Optional complaint ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating complaint processing reports", extra={"complaint_id": complaint_id})

    reports = report_generator.generate_reports(complaint_id=complaint_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "complaint_id": complaint_id,
    }


def main() -> None:
    """Main entry point for complaint processing automation."""
    parser = argparse.ArgumentParser(
        description="Customer complaint processing automation system"
    )
    parser.add_argument(
        "--process",
        nargs=4,
        metavar=("COMPLAINT_ID", "CUSTOMER_ID", "COMPLAINT_TEXT", "CUSTOMER_NAME"),
        help="Process a new complaint",
    )
    parser.add_argument(
        "--resolve",
        nargs=4,
        metavar=("COMPLAINT_ID", "RESOLUTION_TEXT", "RESOLUTION_TYPE", "RESOLVED_BY"),
        help="Resolve a complaint",
    )
    parser.add_argument(
        "--track",
        metavar="COMPLAINT_ID",
        help="Track complaint resolution",
    )
    parser.add_argument(
        "--generate-followup",
        metavar="COMPLAINT_ID",
        help="Generate follow-up for complaint",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--complaint-id",
        help="Filter by complaint ID",
    )
    parser.add_argument(
        "--email",
        help="Customer email",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.process,
        args.resolve,
        args.track,
        args.generate_followup,
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
        if args.process:
            complaint_id, customer_id, complaint_text, customer_name = args.process
            result = process_complaint(
                config=config,
                settings=settings,
                complaint_id=complaint_id,
                customer_id=customer_id,
                complaint_text=complaint_text,
                customer_name=customer_name,
                email=args.email,
            )
            print(f"\nComplaint processed:")
            print(f"Complaint ID: {result['complaint_id']}")
            print(f"Category: {result['category']}")
            print(f"Priority: {result['priority']}")
            print(f"Department: {result.get('department', 'N/A')}")
            print(f"Status: {result.get('status', 'N/A')}")

        if args.resolve:
            complaint_id, resolution_text, resolution_type, resolved_by = args.resolve
            result = resolve_complaint(
                config=config,
                settings=settings,
                complaint_id=complaint_id,
                resolution_text=resolution_text,
                resolution_type=resolution_type,
                resolved_by=resolved_by,
            )
            if result.get("success"):
                print(f"\nComplaint resolved:")
                print(f"Complaint ID: {result['complaint_id']}")
                print(f"Resolution time: {result.get('resolution_time_hours', 0):.1f} hours")

        if args.track:
            result = track_resolution(
                config=config,
                settings=settings,
                complaint_id=args.track,
            )
            print(f"\nResolution tracking:")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Is resolved: {result.get('is_resolved', False)}")
            if result.get("resolution_time_hours"):
                print(f"Resolution time: {result['resolution_time_hours']:.1f} hours")

        if args.generate_followup:
            result = generate_followup(
                config=config,
                settings=settings,
                complaint_id=args.generate_followup,
            )
            if result.get("success"):
                print(f"\nFollow-up generated:")
                print(f"Follow-up ID: {result['followup_id']}")
                print(f"Type: {result['followup_type']}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                complaint_id=args.complaint_id,
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
