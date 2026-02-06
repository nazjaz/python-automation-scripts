"""Application error monitoring automation system.

Monitors application error rates, categorizes errors, identifies patterns,
and generates bug reports with reproduction steps and priority rankings.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.bug_report_generator import BugReportGenerator
from src.error_categorizer import ErrorCategorizer
from src.error_monitor import ErrorMonitor
from src.log_parser import LogParser
from src.pattern_identifier import PatternIdentifier
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/error_monitor.log"))
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


def parse_logs(
    config: dict,
    settings: object,
    log_file: Path,
    application: Optional[str] = None,
    environment: Optional[str] = None,
) -> dict:
    """Parse log file and import errors.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        log_file: Path to log file.
        application: Application name.
        environment: Environment name.

    Returns:
        Dictionary with parsing results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    log_parser = LogParser(config.get("parsing", {}))
    categorizer = ErrorCategorizer(config.get("categorization", {}))

    logger.info(f"Parsing log file: {log_file}")

    errors = log_parser.parse_log_file(log_file)

    if not errors:
        logger.warning("No errors found in log file")
        return {"success": True, "imported_count": 0}

    imported_count = 0
    for error in errors:
        try:
            category_info = categorizer.categorize_error(
                error.get("error_message", ""),
                error.get("error_type"),
                error.get("stack_trace"),
            )

            category = db_manager.add_error_category(
                category_info["category"],
                category_info["description"],
            )

            error_log = db_manager.add_error_log(
                error_message=error.get("error_message", ""),
                error_type=error.get("error_type"),
                stack_trace=error.get("stack_trace"),
                application=application or error.get("application"),
                environment=environment or error.get("environment"),
                severity=category_info["severity"],
                user_id=error.get("user_id"),
                request_id=error.get("request_id"),
            )

            db_manager.update_error_category(error_log.id, category.id)
            imported_count += 1

        except Exception as e:
            logger.error(f"Error importing error log: {e}")

    logger.info(f"Imported {imported_count} error logs from log file")

    return {
        "success": True,
        "imported_count": imported_count,
        "log_file": str(log_file),
    }


def analyze_errors(
    config: dict,
    settings: object,
    application: Optional[str] = None,
    environment: Optional[str] = None,
    hours: int = 24,
) -> dict:
    """Analyze errors and identify patterns.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        application: Filter by application.
        environment: Filter by environment.
        hours: Number of hours to analyze.

    Returns:
        Dictionary with analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    pattern_identifier = PatternIdentifier(config.get("pattern_identification", {}))

    from datetime import datetime, timedelta
    from src.database import ErrorLog

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    session = db_manager.get_session()

    try:
        query = session.query(ErrorLog).filter(ErrorLog.timestamp >= cutoff_time)

        if application:
            query = query.filter(ErrorLog.application == application)
        if environment:
            query = query.filter(ErrorLog.environment == environment)

        errors = query.all()

        error_dicts = [
            {
                "id": e.id,
                "error_message": e.error_message,
                "error_type": e.error_type,
                "stack_trace": e.stack_trace,
                "timestamp": e.timestamp,
                "severity": e.severity,
            }
            for e in errors
        ]

        patterns = pattern_identifier.identify_patterns(error_dicts)

        for pattern in patterns:
            pattern_obj = db_manager.add_error_pattern(
                pattern["pattern_name"],
                pattern["error_signature"],
                pattern["pattern_description"],
            )

            matching_errors = [
                e for e in errors if pattern_identifier._create_error_signature(
                    {
                        "error_message": e.error_message,
                        "error_type": e.error_type,
                    }
                ) == pattern["error_signature"]
            ]

            for error in matching_errors:
                db_manager.update_error_pattern(error.id, pattern_obj.id)

        logger.info(f"Identified {len(patterns)} error patterns")

        return {
            "success": True,
            "patterns_identified": len(patterns),
            "errors_analyzed": len(errors),
        }
    finally:
        session.close()


def generate_bug_reports(
    config: dict,
    settings: object,
    application: Optional[str] = None,
    environment: Optional[str] = None,
) -> dict:
    """Generate bug reports from error patterns.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        application: Filter by application.
        environment: Filter by environment.

    Returns:
        Dictionary with bug report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    error_monitor = ErrorMonitor(db_manager, config.get("monitoring", {}))
    bug_report_generator = BugReportGenerator(db_manager, config.get("bug_reports", {}))

    from src.database import ErrorPattern

    session = db_manager.get_session()
    try:
        patterns = session.query(ErrorPattern).all()

        error_rate_info = error_monitor.calculate_error_rate(application, environment, hours=1)
        error_rate = error_rate_info.get("error_rate", 0.0)

        pattern_dicts = [
            {
                "id": p.id,
                "pattern_name": p.pattern_name,
                "error_signature": p.error_signature,
                "frequency": p.frequency,
                "first_seen": p.first_seen,
                "last_seen": p.last_seen,
                "trend": p.trend,
            }
            for p in patterns
        ]

        bug_reports = bug_report_generator.generate_reports_for_patterns(
            pattern_dicts, error_rate
        )

        logger.info(f"Generated {len(bug_reports)} bug reports")

        return {
            "success": True,
            "bug_reports_generated": len(bug_reports),
            "error_rate": error_rate,
        }
    finally:
        session.close()


def generate_reports(
    config: dict,
    settings: object,
    application: Optional[str] = None,
    environment: Optional[str] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        application: Filter by application.
        environment: Filter by environment.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating error analysis reports", extra={"application": application, "environment": environment})

    reports = report_generator.generate_reports(application=application, environment=environment)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "application": application,
        "environment": environment,
    }


def main() -> None:
    """Main entry point for error monitoring automation."""
    parser = argparse.ArgumentParser(description="Application error monitoring automation system")
    parser.add_argument(
        "--parse",
        type=Path,
        metavar="LOG_FILE",
        help="Parse log file and import errors",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze errors and identify patterns",
    )
    parser.add_argument(
        "--generate-bugs",
        action="store_true",
        help="Generate bug reports from error patterns",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--application",
        help="Filter by application name",
    )
    parser.add_argument(
        "--environment",
        help="Filter by environment (production, staging, development)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to analyze (default: 24)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([args.parse, args.analyze, args.generate_bugs, args.report]):
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
        if args.parse:
            result = parse_logs(
                config=config,
                settings=settings,
                log_file=args.parse,
                application=args.application,
                environment=args.environment,
            )
            print(f"\nLog parsing completed:")
            print(f"Imported errors: {result['imported_count']}")
            print(f"Log file: {result['log_file']}")

        if args.analyze:
            result = analyze_errors(
                config=config,
                settings=settings,
                application=args.application,
                environment=args.environment,
                hours=args.hours,
            )
            print(f"\nError analysis completed:")
            print(f"Patterns identified: {result['patterns_identified']}")
            print(f"Errors analyzed: {result['errors_analyzed']}")

        if args.generate_bugs:
            result = generate_bug_reports(
                config=config,
                settings=settings,
                application=args.application,
                environment=args.environment,
            )
            print(f"\nBug report generation completed:")
            print(f"Bug reports generated: {result['bug_reports_generated']}")
            print(f"Error rate: {result['error_rate']:.2f}%")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                application=args.application,
                environment=args.environment,
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
