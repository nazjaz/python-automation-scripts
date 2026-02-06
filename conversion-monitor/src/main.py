"""Website conversion monitoring automation system.

Monitors website conversion rates, tracks user journeys, identifies drop-off points,
and generates optimization recommendations for improving conversions.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.event_processor import EventProcessor
from src.conversion_monitor import ConversionMonitor
from src.journey_tracker import JourneyTracker
from src.dropoff_identifier import DropOffIdentifier
from src.optimization_recommender import OptimizationRecommender
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/conversion_monitor.log"))
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
    domain: str,
    website_name: Optional[str] = None,
) -> dict:
    """Add a new website.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        domain: Website domain.
        website_name: Website name.

    Returns:
        Dictionary with website information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    logger.info(f"Adding website: {domain}")

    website = db_manager.add_website(domain=domain, website_name=website_name)

    logger.info(f"Website added: ID {website.id}")

    return {
        "success": True,
        "website_id": website.id,
        "domain": website.domain,
    }


def add_conversion_goal(
    config: dict,
    settings: object,
    website_id: int,
    goal_name: str,
    goal_type: str,
    target_url: Optional[str] = None,
    target_event: Optional[str] = None,
) -> dict:
    """Add conversion goal.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.
        goal_name: Goal name.
        goal_type: Goal type.
        target_url: Target URL.
        target_event: Target event.

    Returns:
        Dictionary with goal information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)

    logger.info(f"Adding conversion goal: {goal_name}")

    goal = db_manager.add_conversion_goal(
        website_id=website_id,
        goal_name=goal_name,
        goal_type=goal_type,
        target_url=target_url,
        target_event=target_event,
    )

    logger.info(f"Conversion goal added: ID {goal.id}")

    return {
        "success": True,
        "goal_id": goal.id,
        "goal_name": goal.goal_name,
    }


def import_events(
    config: dict,
    settings: object,
    website_id: int,
    file_path: Path,
    file_format: str = "json",
) -> dict:
    """Import events from file.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.
        file_path: Path to events file.
        file_format: File format (json or csv).

    Returns:
        Dictionary with import results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    event_processor = EventProcessor(db_manager, config.get("events", {}))

    logger.info(f"Importing events from {file_format} file: {file_path}")

    result = event_processor.import_events_from_file(
        website_id=website_id, file_path=str(file_path), file_format=file_format
    )

    logger.info(f"Imported {result['imported_count']} events")

    return result


def monitor_conversion(
    config: dict,
    settings: object,
    website_id: int,
    conversion_goal_id: Optional[int] = None,
    hours: Optional[int] = None,
) -> dict:
    """Monitor conversion rates.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.
        conversion_goal_id: Optional conversion goal ID.
        hours: Number of hours to analyze.

    Returns:
        Dictionary with monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = ConversionMonitor(db_manager, config.get("monitoring", {}))

    logger.info("Calculating conversion rates", extra={"website_id": website_id, "conversion_goal_id": conversion_goal_id})

    conversion_rate = monitor.calculate_conversion_rate(
        website_id=website_id,
        conversion_goal_id=conversion_goal_id,
        hours=hours,
    )

    logger.info(f"Conversion rate: {conversion_rate.get('conversion_rate', 0.0):.2f}%")

    return {
        "success": True,
        "conversion_rate": conversion_rate.get("conversion_rate", 0.0),
        "total_sessions": conversion_rate.get("total_sessions", 0),
        "converted_sessions": conversion_rate.get("converted_sessions", 0),
    }


def track_journeys(
    config: dict,
    settings: object,
    website_id: int,
) -> dict:
    """Track user journeys.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.

    Returns:
        Dictionary with journey tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = JourneyTracker(db_manager, config.get("journey_tracking", {}))

    logger.info(f"Tracking user journeys for website {website_id}")

    common_journeys = tracker.get_common_journeys(website_id, limit=10)
    stats = tracker.get_journey_statistics(website_id)

    logger.info(f"Identified {len(common_journeys)} common journey patterns")

    return {
        "success": True,
        "common_journeys": len(common_journeys),
        "total_journeys": stats.get("total_journeys", 0),
        "average_journey_length": stats.get("average_journey_length", 0.0),
    }


def identify_dropoffs(
    config: dict,
    settings: object,
    website_id: int,
    conversion_goal_id: Optional[int] = None,
) -> dict:
    """Identify drop-off points.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.
        conversion_goal_id: Optional conversion goal ID.

    Returns:
        Dictionary with drop-off identification results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    identifier = DropOffIdentifier(db_manager, config.get("dropoff_detection", {}))

    logger.info("Identifying drop-off points", extra={"website_id": website_id, "conversion_goal_id": conversion_goal_id})

    dropoffs = identifier.identify_dropoffs(
        website_id=website_id, conversion_goal_id=conversion_goal_id
    )

    logger.info(f"Identified {len(dropoffs)} drop-off points")

    return {
        "success": True,
        "dropoff_points_identified": len(dropoffs),
        "dropoffs": dropoffs,
    }


def generate_recommendations(
    config: dict,
    settings: object,
    website_id: int,
    conversion_goal_id: Optional[int] = None,
) -> dict:
    """Generate optimization recommendations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Website ID.
        conversion_goal_id: Optional conversion goal ID.

    Returns:
        Dictionary with recommendation generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    recommender = OptimizationRecommender(
        db_manager, config.get("recommendations", {})
    )

    logger.info("Generating optimization recommendations", extra={"website_id": website_id, "conversion_goal_id": conversion_goal_id})

    recommendations = recommender.generate_recommendations(
        website_id=website_id, conversion_goal_id=conversion_goal_id
    )

    logger.info(f"Generated {len(recommendations)} recommendations")

    return {
        "success": True,
        "recommendations_generated": len(recommendations),
        "recommendations": recommendations,
    }


def generate_reports(
    config: dict,
    settings: object,
    website_id: Optional[int] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        website_id: Optional website ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating conversion monitoring reports", extra={"website_id": website_id})

    reports = report_generator.generate_reports(website_id=website_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "website_id": website_id,
    }


def main() -> None:
    """Main entry point for conversion monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Website conversion monitoring automation system"
    )
    parser.add_argument(
        "--add-website",
        nargs=2,
        metavar=("DOMAIN", "NAME"),
        help="Add a new website",
    )
    parser.add_argument(
        "--add-goal",
        nargs=3,
        metavar=("WEBSITE_ID", "GOAL_NAME", "GOAL_TYPE"),
        help="Add conversion goal",
    )
    parser.add_argument(
        "--import-events",
        nargs=2,
        metavar=("WEBSITE_ID", "FILE"),
        help="Import events from JSON or CSV file",
    )
    parser.add_argument(
        "--monitor",
        type=int,
        metavar="WEBSITE_ID",
        help="Monitor conversion rates",
    )
    parser.add_argument(
        "--track-journeys",
        type=int,
        metavar="WEBSITE_ID",
        help="Track user journeys",
    )
    parser.add_argument(
        "--identify-dropoffs",
        type=int,
        metavar="WEBSITE_ID",
        help="Identify drop-off points",
    )
    parser.add_argument(
        "--generate-recommendations",
        type=int,
        metavar="WEBSITE_ID",
        help="Generate optimization recommendations",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--website-id",
        type=int,
        help="Filter by website ID",
    )
    parser.add_argument(
        "--conversion-goal-id",
        type=int,
        help="Filter by conversion goal ID",
    )
    parser.add_argument(
        "--hours",
        type=int,
        help="Number of hours to analyze",
    )
    parser.add_argument(
        "--target-url",
        help="Target URL for conversion goal",
    )
    parser.add_argument(
        "--target-event",
        help="Target event for conversion goal",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="File format for import (default: json)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.add_website,
        args.add_goal,
        args.import_events,
        args.monitor,
        args.track_journeys,
        args.identify_dropoffs,
        args.generate_recommendations,
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
        if args.add_website:
            domain, name = args.add_website
            result = add_website(
                config=config,
                settings=settings,
                domain=domain,
                website_name=name,
            )
            print(f"\nWebsite added:")
            print(f"ID: {result['website_id']}")
            print(f"Domain: {result['domain']}")

        if args.add_goal:
            website_id, goal_name, goal_type = args.add_goal
            result = add_conversion_goal(
                config=config,
                settings=settings,
                website_id=int(website_id),
                goal_name=goal_name,
                goal_type=goal_type,
                target_url=args.target_url,
                target_event=args.target_event,
            )
            print(f"\nConversion goal added:")
            print(f"ID: {result['goal_id']}")
            print(f"Name: {result['goal_name']}")

        if args.import_events:
            website_id, file_path = args.import_events
            result = import_events(
                config=config,
                settings=settings,
                website_id=int(website_id),
                file_path=Path(file_path),
                file_format=args.format,
            )
            print(f"\nEvent import completed:")
            print(f"Imported events: {result['imported_count']}")
            print(f"File: {result['file_path']}")

        if args.monitor:
            result = monitor_conversion(
                config=config,
                settings=settings,
                website_id=args.monitor,
                conversion_goal_id=args.conversion_goal_id,
                hours=args.hours,
            )
            print(f"\nConversion monitoring completed:")
            print(f"Conversion rate: {result['conversion_rate']:.2f}%")
            print(f"Total sessions: {result['total_sessions']}")
            print(f"Converted sessions: {result['converted_sessions']}")

        if args.track_journeys:
            result = track_journeys(
                config=config,
                settings=settings,
                website_id=args.track_journeys,
            )
            print(f"\nJourney tracking completed:")
            print(f"Common journeys: {result['common_journeys']}")
            print(f"Total journeys: {result['total_journeys']}")

        if args.identify_dropoffs:
            result = identify_dropoffs(
                config=config,
                settings=settings,
                website_id=args.identify_dropoffs,
                conversion_goal_id=args.conversion_goal_id,
            )
            print(f"\nDrop-off identification completed:")
            print(f"Drop-off points identified: {result['dropoff_points_identified']}")

        if args.generate_recommendations:
            result = generate_recommendations(
                config=config,
                settings=settings,
                website_id=args.generate_recommendations,
                conversion_goal_id=args.conversion_goal_id,
            )
            print(f"\nRecommendations generated: {result['recommendations_generated']}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                website_id=args.website_id,
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
