"""Data pipeline monitoring automation system.

Monitors data pipeline health, detects failures, identifies data quality issues,
and automatically triggers remediation workflows with alerting.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.pipeline_monitor import PipelineMonitor
from src.failure_detector import FailureDetector
from src.data_quality_checker import DataQualityChecker
from src.remediation_workflow import RemediationWorkflow
from src.alerting import Alerting
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/pipeline_monitor.log"))
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


def monitor_pipelines(
    config: dict,
    settings: object,
    pipeline_id: Optional[int] = None,
) -> dict:
    """Monitor pipeline health.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        pipeline_id: Optional pipeline ID to filter by.

    Returns:
        Dictionary with monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    monitor = PipelineMonitor(db_manager, config.get("monitoring", {}))

    if pipeline_id:
        logger.info(f"Monitoring pipeline {pipeline_id}")
        health = monitor.check_pipeline_health(pipeline_id)
        return {
            "success": True,
            "pipelines_checked": 1,
            "health_statuses": [health],
        }
    else:
        logger.info("Monitoring all pipelines")
        health_statuses = monitor.monitor_all_pipelines()
        return {
            "success": True,
            "pipelines_checked": len(health_statuses),
            "health_statuses": health_statuses,
        }


def detect_failures(
    config: dict,
    settings: object,
    pipeline_id: Optional[int] = None,
    hours: int = 1,
) -> dict:
    """Detect pipeline failures.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        pipeline_id: Optional pipeline ID to filter by.
        hours: Number of hours to check.

    Returns:
        Dictionary with failure detection results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    failure_detector = FailureDetector(db_manager, config.get("failure_detection", {}))

    logger.info("Detecting pipeline failures", extra={"pipeline_id": pipeline_id, "hours": hours})

    failures = failure_detector.detect_failures(pipeline_id=pipeline_id, hours=hours)

    logger.info(f"Detected {len(failures)} failures")

    return {
        "success": True,
        "failures_detected": len(failures),
        "failures": failures,
    }


def check_quality(
    config: dict,
    settings: object,
    pipeline_id: int,
) -> dict:
    """Check data quality.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        pipeline_id: Pipeline ID.

    Returns:
        Dictionary with quality check results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    quality_checker = DataQualityChecker(
        db_manager, config.get("quality_checks", {})
    )

    logger.info(f"Running quality checks for pipeline {pipeline_id}")

    check_results = quality_checker.run_quality_checks(pipeline_id)

    logger.info(f"Completed {len(check_results)} quality checks")

    return {
        "success": True,
        "checks_run": len(check_results),
        "check_results": check_results,
    }


def trigger_remediation(
    config: dict,
    settings: object,
    pipeline_id: int,
    failure_id: Optional[int] = None,
    auto: bool = False,
) -> dict:
    """Trigger remediation workflow.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        pipeline_id: Pipeline ID.
        failure_id: Optional failure ID.
        auto: If True, auto-remediate all open failures.

    Returns:
        Dictionary with remediation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    remediation = RemediationWorkflow(
        db_manager, config.get("remediation", {})
    )

    if auto:
        logger.info("Auto-remediating all open failures", extra={"pipeline_id": pipeline_id})
        results = remediation.auto_remediate_failures(pipeline_id=pipeline_id)
        return {
            "success": True,
            "workflows_triggered": len(results),
            "results": results,
        }
    else:
        logger.info("Triggering remediation workflow", extra={"pipeline_id": pipeline_id, "failure_id": failure_id})
        result = remediation.trigger_remediation(
            pipeline_id=pipeline_id, failure_id=failure_id
        )
        return {
            "success": result.get("success", False),
            "workflow_id": result.get("workflow_id"),
            "result": result.get("result"),
        }


def send_alerts(
    config: dict,
    settings: object,
    pipeline_id: Optional[int] = None,
) -> dict:
    """Send alerts for issues.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        pipeline_id: Optional pipeline ID to filter by.

    Returns:
        Dictionary with alerting results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    alerting = Alerting(db_manager, config.get("alerting", {}))

    logger.info("Checking for issues requiring alerts", extra={"pipeline_id": pipeline_id})

    open_failures = db_manager.get_open_failures(pipeline_id=pipeline_id)
    alerts_sent = 0

    for failure in open_failures:
        alert = alerting.alert_on_failure(
            pipeline_id=failure.pipeline_id,
            failure_type=failure.failure_type,
            error_message=failure.error_message,
            severity=failure.severity,
        )
        if alert:
            alerts_sent += 1

    logger.info(f"Sent {alerts_sent} alerts")

    return {
        "success": True,
        "alerts_sent": alerts_sent,
    }


def generate_reports(
    config: dict,
    settings: object,
    pipeline_id: Optional[int] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        pipeline_id: Optional pipeline ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating pipeline monitoring reports", extra={"pipeline_id": pipeline_id})

    reports = report_generator.generate_reports(pipeline_id=pipeline_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "pipeline_id": pipeline_id,
    }


def main() -> None:
    """Main entry point for data pipeline monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Data pipeline monitoring automation system"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor pipeline health",
    )
    parser.add_argument(
        "--detect-failures",
        action="store_true",
        help="Detect pipeline failures",
    )
    parser.add_argument(
        "--check-quality",
        type=int,
        metavar="PIPELINE_ID",
        help="Check data quality for pipeline",
    )
    parser.add_argument(
        "--remediate",
        type=int,
        metavar="PIPELINE_ID",
        help="Trigger remediation workflow",
    )
    parser.add_argument(
        "--auto-remediate",
        action="store_true",
        help="Auto-remediate all open failures",
    )
    parser.add_argument(
        "--alert",
        action="store_true",
        help="Send alerts for issues",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--pipeline-id",
        type=int,
        help="Filter by pipeline ID",
    )
    parser.add_argument(
        "--failure-id",
        type=int,
        help="Failure ID for remediation",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=1,
        help="Number of hours to analyze (default: 1)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.monitor,
        args.detect_failures,
        args.check_quality,
        args.remediate,
        args.auto_remediate,
        args.alert,
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
        if args.monitor:
            result = monitor_pipelines(
                config=config,
                settings=settings,
                pipeline_id=args.pipeline_id,
            )
            print(f"\nPipeline monitoring completed:")
            print(f"Pipelines checked: {result['pipelines_checked']}")
            for health in result["health_statuses"]:
                print(f"  {health.get('pipeline_name', 'Unknown')}: {health.get('health_status', 'unknown')}")

        if args.detect_failures:
            result = detect_failures(
                config=config,
                settings=settings,
                pipeline_id=args.pipeline_id,
                hours=args.hours,
            )
            print(f"\nFailure detection completed:")
            print(f"Failures detected: {result['failures_detected']}")

        if args.check_quality:
            result = check_quality(
                config=config,
                settings=settings,
                pipeline_id=args.check_quality,
            )
            print(f"\nQuality checks completed:")
            print(f"Checks run: {result['checks_run']}")

        if args.remediate:
            result = trigger_remediation(
                config=config,
                settings=settings,
                pipeline_id=args.remediate,
                failure_id=args.failure_id,
            )
            print(f"\nRemediation triggered:")
            print(f"Success: {result['success']}")
            if result.get("workflow_id"):
                print(f"Workflow ID: {result['workflow_id']}")

        if args.auto_remediate:
            result = trigger_remediation(
                config=config,
                settings=settings,
                pipeline_id=args.pipeline_id,
                auto=True,
            )
            print(f"\nAuto-remediation completed:")
            print(f"Workflows triggered: {result['workflows_triggered']}")

        if args.alert:
            result = send_alerts(
                config=config,
                settings=settings,
                pipeline_id=args.pipeline_id,
            )
            print(f"\nAlerts sent: {result['alerts_sent']}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                pipeline_id=args.pipeline_id,
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
