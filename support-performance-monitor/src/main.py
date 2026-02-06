"""Support performance monitoring automation system.

Monitors customer support response times, tracks resolution rates,
identifies bottlenecks, and generates performance dashboards for management.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.bottleneck_identifier import BottleneckIdentifier
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.dashboard_generator import DashboardGenerator
from src.resolution_rate_analyzer import ResolutionRateAnalyzer
from src.response_time_tracker import ResponseTimeTracker


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/support_performance.log"))
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


def add_ticket(
    config: dict,
    settings: object,
    ticket_number: str,
    title: str,
    category: str,
    priority: str,
    customer_email: str,
    description: Optional[str] = None,
    assigned_agent: Optional[str] = None,
) -> dict:
    """Add a support ticket.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        ticket_number: Unique ticket number.
        title: Ticket title.
        category: Ticket category.
        priority: Priority level.
        customer_email: Customer email address.
        description: Optional ticket description.
        assigned_agent: Optional assigned agent.

    Returns:
        Dictionary with ticket information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    ticket = db_manager.add_ticket(
        ticket_number=ticket_number,
        title=title,
        category=category,
        priority=priority,
        customer_email=customer_email,
        description=description,
        assigned_agent=assigned_agent,
    )

    logger.info(
        f"Added ticket: {ticket_number}",
        extra={"ticket_id": ticket.id, "ticket_number": ticket_number},
    )

    return {
        "success": True,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
    }


def track_response_times(
    config: dict,
    settings: object,
    days: Optional[int] = None,
) -> dict:
    """Track response times for tickets.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        days: Optional number of days to look back.

    Returns:
        Dictionary with tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ResponseTimeTracker(db_manager, config)

    logger.info("Tracking response times", extra={"days": days})

    tracked_count = tracker.track_all_tickets(days=days)

    logger.info(
        f"Response time tracking completed: {tracked_count} tickets processed",
        extra={"tracked_count": tracked_count},
    )

    return {
        "success": True,
        "tracked_count": tracked_count,
    }


def analyze_resolution_rates(
    config: dict,
    settings: object,
    days: int = 30,
    category: Optional[str] = None,
    agent: Optional[str] = None,
) -> dict:
    """Analyze resolution rates.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        days: Number of days to analyze.
        category: Optional category filter.
        agent: Optional agent filter.

    Returns:
        Dictionary with analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = ResolutionRateAnalyzer(db_manager, config)

    logger.info("Analyzing resolution rates", extra={"days": days, "category": category, "agent": agent})

    resolution_data = analyzer.calculate_resolution_rate(
        days=days, category=category, agent=agent
    )

    logger.info(
        f"Resolution rate analysis completed",
        extra={
            "resolution_rate": resolution_data["resolution_rate"],
            "total_tickets": resolution_data["total_tickets"],
        },
    )

    return {
        "success": True,
        "total_tickets": resolution_data["total_tickets"],
        "resolved_tickets": resolution_data["resolved_tickets"],
        "resolution_rate": resolution_data["resolution_rate"],
        "average_resolution_time_hours": resolution_data.get(
            "average_resolution_time_hours"
        ),
    }


def identify_bottlenecks(
    config: dict,
    settings: object,
    days: int = 30,
) -> dict:
    """Identify bottlenecks in support operations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        days: Number of days to analyze.

    Returns:
        Dictionary with bottleneck identification results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    identifier = BottleneckIdentifier(db_manager, config)

    logger.info("Identifying bottlenecks", extra={"days": days})

    bottlenecks = identifier.identify_all_bottlenecks(days=days)

    logger.info(
        f"Bottleneck identification completed: {len(bottlenecks)} bottlenecks found",
        extra={"bottleneck_count": len(bottlenecks)},
    )

    return {
        "success": True,
        "bottleneck_count": len(bottlenecks),
        "bottlenecks": [
            {
                "type": b.bottleneck_type,
                "identifier": b.identifier,
                "severity": b.severity,
                "description": b.description,
            }
            for b in bottlenecks
        ],
    }


def generate_dashboard(
    config: dict,
    settings: object,
    days: int = 30,
) -> dict:
    """Generate performance dashboard.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        days: Number of days to analyze.

    Returns:
        Dictionary with dashboard paths.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = DashboardGenerator(
        db_manager,
        config,
        output_dir=config.get("dashboard", {}).get("output_directory", "dashboards"),
    )

    logger.info("Generating performance dashboard", extra={"days": days})

    reports = {}

    if config.get("dashboard", {}).get("generate_html", True):
        reports["html"] = str(generator.generate_html_dashboard(days=days))

    if config.get("dashboard", {}).get("generate_csv", True):
        reports["csv"] = str(generator.generate_csv_dashboard(days=days))

    logger.info(
        f"Dashboard generated: {len(reports)} report(s)",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": reports,
    }


def main() -> None:
    """Main entry point for support performance monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Support performance monitoring automation system"
    )
    parser.add_argument(
        "--add-ticket",
        action="store_true",
        help="Add a support ticket",
    )
    parser.add_argument(
        "--ticket-number", help="Ticket number"
    )
    parser.add_argument(
        "--title", help="Ticket title"
    )
    parser.add_argument(
        "--category", help="Ticket category"
    )
    parser.add_argument(
        "--priority", help="Priority level (low, medium, high, urgent)"
    )
    parser.add_argument(
        "--customer-email", help="Customer email address"
    )
    parser.add_argument(
        "--description", help="Ticket description"
    )
    parser.add_argument(
        "--assigned-agent", help="Assigned agent"
    )
    parser.add_argument(
        "--track-response-times",
        action="store_true",
        help="Track response times for tickets",
    )
    parser.add_argument(
        "--analyze-resolution",
        action="store_true",
        help="Analyze resolution rates",
    )
    parser.add_argument(
        "--identify-bottlenecks",
        action="store_true",
        help="Identify bottlenecks",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Generate performance dashboard",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.add_ticket,
        args.track_response_times,
        args.analyze_resolution,
        args.identify_bottlenecks,
        args.dashboard,
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
        if args.add_ticket:
            if not all([args.ticket_number, args.title, args.category, args.priority, args.customer_email]):
                print(
                    "Error: --ticket-number, --title, --category, --priority, and --customer-email are required for --add-ticket",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_ticket(
                config=config,
                settings=settings,
                ticket_number=args.ticket_number,
                title=args.title,
                category=args.category,
                priority=args.priority,
                customer_email=args.customer_email,
                description=args.description,
                assigned_agent=args.assigned_agent,
            )

            print(f"\nTicket added successfully:")
            print(f"Ticket ID: {result['ticket_id']}")
            print(f"Ticket Number: {result['ticket_number']}")

        if args.track_response_times:
            result = track_response_times(
                config=config,
                settings=settings,
                days=args.days,
            )
            print(f"\nResponse time tracking completed:")
            print(f"Tickets processed: {result['tracked_count']}")

        if args.analyze_resolution:
            result = analyze_resolution_rates(
                config=config,
                settings=settings,
                days=args.days,
            )
            print(f"\nResolution rate analysis:")
            print(f"Total tickets: {result['total_tickets']}")
            print(f"Resolved tickets: {result['resolved_tickets']}")
            print(f"Resolution rate: {result['resolution_rate']:.2%}")
            if result.get("average_resolution_time_hours"):
                print(f"Average resolution time: {result['average_resolution_time_hours']:.2f} hours")

        if args.identify_bottlenecks:
            result = identify_bottlenecks(
                config=config,
                settings=settings,
                days=args.days,
            )
            print(f"\nBottleneck identification:")
            print(f"Bottlenecks found: {result['bottleneck_count']}")
            for bottleneck in result["bottlenecks"][:5]:
                print(f"  - {bottleneck['type']}: {bottleneck['identifier']} ({bottleneck['severity']})")

        if args.dashboard:
            result = generate_dashboard(
                config=config,
                settings=settings,
                days=args.days,
            )
            print(f"\nDashboard generated:")
            for report_type, path in result["reports"].items():
                print(f"  {report_type.upper()}: {path}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
