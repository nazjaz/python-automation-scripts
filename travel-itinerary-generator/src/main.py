"""Travel itinerary generator automation system.

Automatically generates personalized travel itineraries by integrating
flight, hotel, and activity bookings, sending reminders, and providing
real-time travel updates.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dateutil import parser as date_parser

from src.activity_service import ActivityService
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.flight_service import FlightService
from src.hotel_service import HotelService
from src.itinerary_generator import ItineraryGenerator
from src.notification_service import NotificationService
from src.reminder_service import ReminderService
from src.update_checker import UpdateChecker


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/itinerary.log"))
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


def create_itinerary(
    traveler_name: str,
    traveler_email: str,
    trip_start_date: datetime,
    trip_end_date: datetime,
    destination: str,
    config: dict,
    settings: object,
    traveler_phone: Optional[str] = None,
) -> dict:
    """Create a complete travel itinerary.

    Args:
        traveler_name: Traveler's full name.
        traveler_email: Traveler's email address.
        trip_start_date: Trip start date and time.
        trip_end_date: Trip end date and time.
        destination: Trip destination.
        config: Configuration dictionary.
        settings: Application settings.
        traveler_phone: Traveler's phone number (optional).

    Returns:
        Dictionary with itinerary creation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(config.get("database", {}).get("url", "sqlite:///itineraries.db"))
    db_manager.create_tables()

    itinerary_config = config.get("itinerary", {})
    flight_config = config.get("flights", {})
    hotel_config = config.get("hotels", {})
    activity_config = config.get("activities", {})
    notification_config = config.get("notifications", {}).get("email", {})

    flight_service = FlightService(
        db_manager,
        settings.flight_api_key,
        settings.flight_api_secret,
        flight_config.get("api_provider", "amadeus"),
    )

    hotel_service = HotelService(
        db_manager,
        settings.hotel_api_key,
        hotel_config.get("api_provider", "booking"),
    )

    activity_service = ActivityService(
        db_manager,
        settings.activity_api_key,
        activity_config.get("api_provider", "tripadvisor"),
    )

    notification_service = NotificationService(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_username,
        settings.smtp_password,
        settings.smtp_from_email,
        notification_config.get("from_name", "Travel Itinerary Service"),
    )

    reminder_service = ReminderService(
        db_manager,
        notification_service,
        itinerary_config.get("reminder_hours_before", [72, 24, 2]),
    )

    itinerary = db_manager.create_itinerary(
        traveler_name=traveler_name,
        traveler_email=traveler_email,
        trip_start_date=trip_start_date,
        trip_end_date=trip_end_date,
        destination=destination,
        traveler_phone=traveler_phone,
        timezone=itinerary_config.get("default_timezone", "UTC"),
    )

    logger.info(f"Created itinerary {itinerary.id} for {traveler_name}")

    reminder_service.schedule_reminders(itinerary.id)

    generator = ItineraryGenerator(
        db_manager,
        output_directory=itinerary_config.get("output_directory", "itineraries"),
    )

    output_formats = itinerary_config.get("output_format", ["html", "pdf"])
    generated_files = []

    if "html" in output_formats:
        html_path = generator.generate_html(itinerary.id)
        generated_files.append(str(html_path))

    if "pdf" in output_formats:
        pdf_path = generator.generate_pdf(itinerary.id)
        generated_files.append(str(pdf_path))

    return {
        "itinerary_id": itinerary.id,
        "traveler_name": traveler_name,
        "destination": destination,
        "generated_files": generated_files,
        "success": True,
    }


def process_reminders(config: dict, settings: object) -> int:
    """Process and send due reminders.

    Args:
        config: Configuration dictionary.
        settings: Application settings.

    Returns:
        Number of reminders sent.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(config.get("database", {}).get("url", "sqlite:///itineraries.db"))
    notification_config = config.get("notifications", {}).get("email", {})

    notification_service = NotificationService(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_username,
        settings.smtp_password,
        settings.smtp_from_email,
        notification_config.get("from_name", "Travel Itinerary Service"),
    )

    itinerary_config = config.get("itinerary", {})
    reminder_service = ReminderService(
        db_manager,
        notification_service,
        itinerary_config.get("reminder_hours_before", [72, 24, 2]),
    )

    sent_count = reminder_service.process_due_reminders()
    logger.info(f"Sent {sent_count} reminders")
    return sent_count


def check_updates(config: dict, settings: object) -> int:
    """Check for travel updates.

    Args:
        config: Configuration dictionary.
        settings: Application settings.

    Returns:
        Number of updates found.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(config.get("database", {}).get("url", "sqlite:///itineraries.db"))
    notification_config = config.get("notifications", {}).get("email", {})

    flight_service = FlightService(
        db_manager,
        settings.flight_api_key,
        settings.flight_api_secret,
        config.get("flights", {}).get("api_provider", "amadeus"),
    )

    notification_service = NotificationService(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_username,
        settings.smtp_password,
        settings.smtp_from_email,
        notification_config.get("from_name", "Travel Itinerary Service"),
    )

    update_checker = UpdateChecker(db_manager, flight_service, notification_service)
    update_count = update_checker.check_all_updates()

    logger.info(f"Found {update_count} updates")
    return update_count


def main() -> None:
    """Main entry point for travel itinerary generator."""
    parser = argparse.ArgumentParser(description="Travel itinerary generator")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument("--create", action="store_true", help="Create new itinerary")
    parser.add_argument("--name", help="Traveler name (required for create)")
    parser.add_argument("--email", help="Traveler email (required for create)")
    parser.add_argument("--phone", help="Traveler phone (optional)")
    parser.add_argument("--start-date", help="Trip start date (YYYY-MM-DD HH:MM)")
    parser.add_argument("--end-date", help="Trip end date (YYYY-MM-DD HH:MM)")
    parser.add_argument("--destination", help="Trip destination (required for create)")
    parser.add_argument("--reminders", action="store_true", help="Process reminders")
    parser.add_argument("--updates", action="store_true", help="Check for updates")

    args = parser.parse_args()

    try:
        config = load_config(args.config) if args.config else load_config()
        settings = get_settings()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.get("logging", {}))

    logger = logging.getLogger(__name__)

    if args.create:
        if not all([args.name, args.email, args.start_date, args.end_date, args.destination]):
            print("Error: --name, --email, --start-date, --end-date, and --destination are required for --create", file=sys.stderr)
            sys.exit(1)

        try:
            start_date = date_parser.parse(args.start_date)
            end_date = date_parser.parse(args.end_date)
        except Exception as e:
            print(f"Error parsing dates: {e}", file=sys.stderr)
            sys.exit(1)

        result = create_itinerary(
            traveler_name=args.name,
            traveler_email=args.email,
            trip_start_date=start_date,
            trip_end_date=end_date,
            destination=args.destination,
            config=config,
            settings=settings,
            traveler_phone=args.phone,
        )

        print(f"\nItinerary created successfully!")
        print(f"Itinerary ID: {result['itinerary_id']}")
        print(f"Traveler: {result['traveler_name']}")
        print(f"Destination: {result['destination']}")
        print(f"Generated files: {', '.join(result['generated_files'])}")

    elif args.reminders:
        sent_count = process_reminders(config, settings)
        print(f"Sent {sent_count} reminders")

    elif args.updates:
        update_count = check_updates(config, settings)
        print(f"Found {update_count} updates")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
