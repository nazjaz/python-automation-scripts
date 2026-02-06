"""Supply chain logistics monitoring automation system.

Monitors supply chain logistics, tracks shipments, predicts delays,
and generates logistics reports with route optimization recommendations.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.shipment_tracker import ShipmentTracker
from src.delay_predictor import DelayPredictor
from src.route_optimizer import RouteOptimizer
from src.logistics_monitor import LogisticsMonitor
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/logistics_monitor.log"))
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


def track_shipment(
    config: dict,
    settings: object,
    shipment_id: str,
) -> dict:
    """Track shipment.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        shipment_id: Shipment identifier.

    Returns:
        Dictionary with tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ShipmentTracker(db_manager, config.get("tracking", {}))

    logger.info(f"Tracking shipment: {shipment_id}")

    tracking_info = tracker.track_shipment(shipment_id)

    logger.info(f"Shipment status: {tracking_info.get('status', 'unknown')}")

    return tracking_info


def predict_delay(
    config: dict,
    settings: object,
    shipment_id: str,
    delay_type: str,
    reason: Optional[str] = None,
) -> dict:
    """Predict delay for shipment.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        shipment_id: Shipment identifier.
        delay_type: Delay type.
        reason: Delay reason.

    Returns:
        Dictionary with delay prediction results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    predictor = DelayPredictor(db_manager, config.get("delay_prediction", {}))

    logger.info(f"Predicting delay for shipment: {shipment_id}")

    prediction = predictor.predict_delay(shipment_id, delay_type, reason)

    logger.info(
        f"Predicted delay: {prediction.get('predicted_delay_hours', 0):.1f} hours"
    )

    return prediction


def optimize_route(
    config: dict,
    settings: object,
    shipment_id: str,
) -> dict:
    """Optimize route for shipment.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        shipment_id: Shipment identifier.

    Returns:
        Dictionary with route optimization results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    optimizer = RouteOptimizer(db_manager, config.get("route_optimization", {}))

    logger.info(f"Optimizing route for shipment: {shipment_id}")

    optimization = optimizer.optimize_route(shipment_id)

    logger.info("Route optimization completed")

    return optimization


def monitor_logistics(
    config: dict,
    settings: object,
    days: Optional[int] = None,
) -> dict:
    """Monitor logistics performance.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        days: Number of days to analyze.

    Returns:
        Dictionary with monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = LogisticsMonitor(db_manager, config.get("monitoring", {}))

    logger.info("Monitoring logistics performance", extra={"days": days})

    summary = monitor.monitor_logistics(days=days)
    trends = monitor.get_logistics_trends(days=days or 30)

    logger.info(
        f"On-time percentage: {summary.get('on_time_percentage', 0.0):.2f}%"
    )

    return {
        "summary": summary,
        "trends": trends,
    }


def generate_reports(
    config: dict,
    settings: object,
    shipment_id: Optional[str] = None,
) -> dict:
    """Generate logistics reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        shipment_id: Optional shipment ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating logistics reports", extra={"shipment_id": shipment_id})

    reports = report_generator.generate_reports(shipment_id=shipment_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "shipment_id": shipment_id,
    }


def main() -> None:
    """Main entry point for logistics monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Supply chain logistics monitoring automation system"
    )
    parser.add_argument(
        "--track",
        metavar="SHIPMENT_ID",
        help="Track shipment",
    )
    parser.add_argument(
        "--predict-delay",
        nargs=2,
        metavar=("SHIPMENT_ID", "DELAY_TYPE"),
        help="Predict delay for shipment",
    )
    parser.add_argument(
        "--optimize-route",
        metavar="SHIPMENT_ID",
        help="Optimize route for shipment",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor logistics performance",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate logistics reports",
    )
    parser.add_argument(
        "--shipment-id",
        help="Filter by shipment ID",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to analyze",
    )
    parser.add_argument(
        "--delay-reason",
        help="Delay reason",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.track,
        args.predict_delay,
        args.optimize_route,
        args.monitor,
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
        if args.track:
            result = track_shipment(
                config=config,
                settings=settings,
                shipment_id=args.track,
            )
            print(f"\nShipment tracking:")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Current location: {result.get('current_location', 'N/A')}")
            print(f"Estimated delivery: {result.get('estimated_delivery', 'N/A')}")

        if args.predict_delay:
            shipment_id, delay_type = args.predict_delay
            result = predict_delay(
                config=config,
                settings=settings,
                shipment_id=shipment_id,
                delay_type=delay_type,
                reason=args.delay_reason,
            )
            if result.get("predicted_delay_hours"):
                print(f"\nDelay prediction:")
                print(f"Predicted delay: {result['predicted_delay_hours']:.1f} hours")
                print(f"Severity: {result.get('severity', 'unknown')}")
                print(f"Adjusted ETA: {result.get('adjusted_eta', 'N/A')}")

        if args.optimize_route:
            result = optimize_route(
                config=config,
                settings=settings,
                shipment_id=args.optimize_route,
            )
            if result.get("savings"):
                print(f"\nRoute optimization:")
                print(f"Time savings: {result['savings'].get('time_savings_hours', 0):.1f} hours")
                print(f"Distance savings: {result['savings'].get('distance_savings_km', 0):.1f} km")

        if args.monitor:
            result = monitor_logistics(
                config=config,
                settings=settings,
                days=args.days,
            )
            summary = result["summary"]
            print(f"\nLogistics monitoring:")
            print(f"Total shipments: {summary.get('total_shipments', 0)}")
            print(f"On-time percentage: {summary.get('on_time_percentage', 0.0):.2f}%")
            print(f"Average delay: {summary.get('average_delay_hours', 0.0):.1f} hours")
            print(f"Trend: {result['trends'].get('trend', 'unknown')}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                shipment_id=args.shipment_id,
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
