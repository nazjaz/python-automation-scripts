"""Subscription monitor automation system.

Monitors customer subscription renewals, identifies churn risks, triggers retention
campaigns, and tracks subscription lifecycle metrics.
"""

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.campaign_trigger import CampaignTrigger
from src.churn_detector import ChurnDetector
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.metrics_tracker import MetricsTracker
from src.renewal_monitor import RenewalMonitor
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/subscription_monitor.log"))
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


def check_renewals(
    config: dict,
    settings: object,
    days_ahead: int = 30,
) -> dict:
    """Check subscriptions due for renewal.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        days_ahead: Days ahead to check.

    Returns:
        Dictionary with renewal check results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = RenewalMonitor(db_manager, config)

    logger.info("Checking renewals", extra={"days_ahead": days_ahead})

    upcoming_renewals = monitor.identify_upcoming_renewals(days_ahead=days_ahead)

    logger.info(
        f"Found {len(upcoming_renewals)} upcoming renewals",
        extra={"upcoming_renewal_count": len(upcoming_renewals)},
    )

    return {
        "success": True,
        "upcoming_renewals": upcoming_renewals,
    }


def detect_churn_risks(
    config: dict,
    settings: object,
    customer_id: Optional[int] = None,
) -> dict:
    """Detect churn risks.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        customer_id: Optional customer ID filter.

    Returns:
        Dictionary with churn risk detection results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    detector = ChurnDetector(db_manager, config)

    logger.info("Detecting churn risks", extra={"customer_id": customer_id})

    if customer_id:
        risk = detector.assess_churn_risk(customer_id)
        at_risk = [risk]
    else:
        at_risk = detector.identify_at_risk_customers(risk_level="high")

    logger.info(
        f"Detected {len(at_risk)} at-risk customers",
        extra={"at_risk_count": len(at_risk)},
    )

    return {
        "success": True,
        "at_risk_count": len(at_risk),
        "at_risk_customers": [
            {
                "customer_id": r.customer_id,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "factors": r.factors,
            }
            for r in at_risk
        ],
    }


def trigger_campaigns(
    config: dict,
    settings: object,
    customer_id: Optional[int] = None,
) -> dict:
    """Trigger retention campaigns.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        customer_id: Optional customer ID filter.

    Returns:
        Dictionary with campaign triggering results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    trigger = CampaignTrigger(db_manager, config)

    logger.info("Triggering campaigns", extra={"customer_id": customer_id})

    campaigns = trigger.check_and_trigger_campaigns(customer_id=customer_id)

    logger.info(
        f"Triggered {len(campaigns)} campaigns",
        extra={"campaign_count": len(campaigns)},
    )

    return {
        "success": True,
        "campaign_count": len(campaigns),
        "campaigns": [
            {
                "id": c.id,
                "customer_id": c.customer_id,
                "campaign_type": c.campaign_type,
                "triggered_by": c.triggered_by,
            }
            for c in campaigns
        ],
    }


def track_metrics(
    config: dict,
    settings: object,
) -> dict:
    """Track subscription lifecycle metrics.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.

    Returns:
        Dictionary with metrics tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = MetricsTracker(db_manager, config)

    logger.info("Tracking metrics")

    metrics = tracker.track_all_metrics()

    logger.info(
        f"Tracked metrics",
        extra={"metrics": metrics},
    )

    return {
        "success": True,
        "metrics": metrics,
    }


def generate_report(
    config: dict,
    settings: object,
    format: str = "html",
) -> dict:
    """Generate subscription monitoring report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        format: Report format (html or csv).

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

    logger.info("Generating subscription report", extra={"format": format})

    if format == "html":
        report_path = generator.generate_html_report()
    else:
        report_path = generator.generate_csv_report()

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
    """Main entry point for subscription monitor automation."""
    parser = argparse.ArgumentParser(
        description="Subscription monitor automation system"
    )
    parser.add_argument(
        "--check-renewals",
        action="store_true",
        help="Check subscriptions due for renewal",
    )
    parser.add_argument(
        "--days-ahead", type=int, default=30, help="Days ahead to check (default: 30)"
    )
    parser.add_argument(
        "--detect-churn",
        action="store_true",
        help="Detect churn risks",
    )
    parser.add_argument(
        "--customer-id", type=int, help="Customer ID"
    )
    parser.add_argument(
        "--trigger-campaigns",
        action="store_true",
        help="Trigger retention campaigns",
    )
    parser.add_argument(
        "--track-metrics",
        action="store_true",
        help="Track subscription lifecycle metrics",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate subscription monitoring report",
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
        args.check_renewals,
        args.detect_churn,
        args.trigger_campaigns,
        args.track_metrics,
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
        db_manager = DatabaseManager(settings.database.url)
        db_manager.create_tables()

        if args.check_renewals:
            result = check_renewals(
                config=config,
                settings=settings,
                days_ahead=args.days_ahead,
            )

            print(f"\nRenewal Check:")
            print(f"Upcoming renewals: {len(result['upcoming_renewals'])}")
            for renewal in result["upcoming_renewals"][:5]:
                print(f"  - Subscription {renewal['subscription_id']}: ${renewal['amount']:.2f} on {renewal['renewal_date']}")

        elif args.detect_churn:
            result = detect_churn_risks(
                config=config,
                settings=settings,
                customer_id=args.customer_id,
            )

            print(f"\nChurn Risk Detection:")
            print(f"At-risk customers: {result['at_risk_count']}")
            for customer in result["at_risk_customers"][:5]:
                print(f"  - Customer {customer['customer_id']}: {customer['risk_level']} ({customer['risk_score']:.2f})")
                print(f"    Factors: {customer['factors']}")

        elif args.trigger_campaigns:
            result = trigger_campaigns(
                config=config,
                settings=settings,
                customer_id=args.customer_id,
            )

            print(f"\nCampaign Triggering:")
            print(f"Campaigns triggered: {result['campaign_count']}")
            for campaign in result["campaigns"][:5]:
                print(f"  - {campaign['campaign_type']} for customer {campaign['customer_id']} (triggered by: {campaign['triggered_by']})")

        elif args.track_metrics:
            result = track_metrics(
                config=config,
                settings=settings,
            )

            print(f"\nMetrics Tracking:")
            for metric_type, value in result["metrics"].items():
                if isinstance(value, float):
                    if "rate" in metric_type:
                        print(f"  {metric_type.upper()}: {value:.2%}")
                    else:
                        print(f"  {metric_type.upper()}: ${value:.2f}")
                else:
                    print(f"  {metric_type.upper()}: {value}")

        elif args.generate_report:
            result = generate_report(
                config=config,
                settings=settings,
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
