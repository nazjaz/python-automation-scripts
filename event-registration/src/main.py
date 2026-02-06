"""Event registration automation system.

Automatically processes event registrations, sends confirmation emails,
generates attendee lists, creates name badges, and manages waitlists with capacity tracking.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.attendee_list_generator import AttendeeListGenerator
from src.badge_generator import BadgeGenerator
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.email_service import EmailService
from src.registration_processor import RegistrationProcessor


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/event_registration.log"))
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


def create_event(
    config: dict,
    settings: object,
    name: str,
    event_date: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
    capacity: int = 100,
    allow_waitlist: bool = True,
) -> dict:
    """Create a new event.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        name: Event name.
        event_date: Event date and time (ISO format).
        location: Optional event location.
        description: Optional event description.
        capacity: Maximum capacity.
        allow_waitlist: Whether to allow waitlist.

    Returns:
        Dictionary with event information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    try:
        event_datetime = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
    except ValueError:
        try:
            event_datetime = datetime.strptime(event_date, "%Y-%m-%d %H:%M")
        except ValueError:
            logger.error(f"Invalid date format: {event_date}")
            return {"success": False, "error": "Invalid date format. Use ISO format or YYYY-MM-DD HH:MM"}

    event = db_manager.add_event(
        name=name,
        event_date=event_datetime,
        location=location,
        description=description,
        capacity=capacity,
        allow_waitlist=allow_waitlist,
    )

    logger.info(f"Created event: {event.name}", extra={"event_id": event.id, "name": name})

    return {
        "success": True,
        "event_id": event.id,
        "name": event.name,
        "event_date": event.event_date.isoformat(),
    }


def register_attendee(
    config: dict,
    settings: object,
    event_id: int,
    name: str,
    email: str,
    company: Optional[str] = None,
    phone: Optional[str] = None,
    ticket_type: Optional[str] = None,
    dietary_restrictions: Optional[str] = None,
    special_requests: Optional[str] = None,
    send_email: bool = True,
) -> dict:
    """Register an attendee for an event.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        event_id: Event ID.
        name: Registrant name.
        email: Registrant email.
        company: Optional company name.
        phone: Optional phone number.
        ticket_type: Optional ticket type.
        dietary_restrictions: Optional dietary restrictions.
        special_requests: Optional special requests.
        send_email: Whether to send confirmation email.

    Returns:
        Dictionary with registration result.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    processor = RegistrationProcessor(db_manager, config)

    result = processor.process_registration(
        event_id=event_id,
        name=name,
        email=email,
        company=company,
        phone=phone,
        ticket_type=ticket_type,
        dietary_restrictions=dietary_restrictions,
        special_requests=special_requests,
    )

    if not result.get("success"):
        return result

    registration_id = result["registration_id"]

    if send_email:
        email_service = EmailService(db_manager, config)

        if result.get("is_waitlist"):
            email_service.send_waitlist_email(registration_id)
        else:
            email_service.send_confirmation_email(registration_id)

    logger.info(
        f"Registration processed: {email}",
        extra={
            "event_id": event_id,
            "registration_id": registration_id,
            "status": result.get("status"),
        },
    )

    return result


def generate_attendee_list(
    config: dict,
    settings: object,
    event_id: int,
    include_waitlist: bool = False,
    format: str = "csv",
) -> dict:
    """Generate attendee list for event.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        event_id: Event ID.
        include_waitlist: Whether to include waitlist.
        format: Output format (csv or html).

    Returns:
        Dictionary with report path.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = AttendeeListGenerator(db_manager, output_dir="reports")

    logger.info("Generating attendee list", extra={"event_id": event_id, "format": format})

    if format == "html":
        report_path = generator.generate_html_list(
            event_id=event_id, include_waitlist=include_waitlist
        )
    else:
        report_path = generator.generate_csv_list(
            event_id=event_id, include_waitlist=include_waitlist
        )

    logger.info(
        f"Attendee list generated: {report_path}",
        extra={"event_id": event_id, "report_path": str(report_path)},
    )

    return {
        "success": True,
        "report_path": str(report_path),
        "format": format,
    }


def generate_badges(
    config: dict,
    settings: object,
    event_id: int,
    registration_id: Optional[int] = None,
) -> dict:
    """Generate name badges.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        event_id: Event ID.
        registration_id: Optional specific registration ID.

    Returns:
        Dictionary with badge paths.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = BadgeGenerator(db_manager, config)

    logger.info("Generating badges", extra={"event_id": event_id, "registration_id": registration_id})

    if registration_id:
        badge_path = generator.generate_badge(registration_id)
        badge_paths = [badge_path] if badge_path else []
    else:
        badge_paths = generator.generate_badges_for_event(event_id)

    logger.info(
        f"Generated {len(badge_paths)} badges",
        extra={"event_id": event_id, "badge_count": len(badge_paths)},
    )

    return {
        "success": True,
        "badge_count": len(badge_paths),
        "badge_paths": [str(p) for p in badge_paths],
    }


def main() -> None:
    """Main entry point for event registration automation."""
    parser = argparse.ArgumentParser(
        description="Event registration automation system"
    )
    parser.add_argument(
        "--create-event",
        action="store_true",
        help="Create a new event",
    )
    parser.add_argument(
        "--name", help="Event name or registrant name"
    )
    parser.add_argument(
        "--event-date", help="Event date and time (ISO format or YYYY-MM-DD HH:MM)"
    )
    parser.add_argument(
        "--location", help="Event location"
    )
    parser.add_argument(
        "--description", help="Event description"
    )
    parser.add_argument(
        "--capacity", type=int, default=100, help="Event capacity (default: 100)"
    )
    parser.add_argument(
        "--allow-waitlist",
        action="store_true",
        default=True,
        help="Allow waitlist (default: True)",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register an attendee",
    )
    parser.add_argument(
        "--event-id", type=int, help="Event ID"
    )
    parser.add_argument(
        "--email", help="Registrant email address"
    )
    parser.add_argument(
        "--company", help="Company name"
    )
    parser.add_argument(
        "--phone", help="Phone number"
    )
    parser.add_argument(
        "--ticket-type", help="Ticket type"
    )
    parser.add_argument(
        "--dietary-restrictions", help="Dietary restrictions"
    )
    parser.add_argument(
        "--special-requests", help="Special requests"
    )
    parser.add_argument(
        "--generate-list",
        action="store_true",
        help="Generate attendee list",
    )
    parser.add_argument(
        "--include-waitlist",
        action="store_true",
        help="Include waitlist in attendee list",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "html"],
        default="csv",
        help="Attendee list format (default: csv)",
    )
    parser.add_argument(
        "--generate-badges",
        action="store_true",
        help="Generate name badges",
    )
    parser.add_argument(
        "--registration-id", type=int, help="Specific registration ID for badge generation"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.create_event,
        args.register,
        args.generate_list,
        args.generate_badges,
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
        if args.create_event:
            if not args.name or not args.event_date:
                print("Error: --name and --event-date are required for --create-event", file=sys.stderr)
                sys.exit(1)

            result = create_event(
                config=config,
                settings=settings,
                name=args.name,
                event_date=args.event_date,
                location=args.location,
                description=args.description,
                capacity=args.capacity,
                allow_waitlist=args.allow_waitlist,
            )

            if result["success"]:
                print(f"\nEvent created successfully:")
                print(f"ID: {result['event_id']}")
                print(f"Name: {result['name']}")
                print(f"Date: {result['event_date']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.register:
            if not args.event_id or not args.name or not args.email:
                print(
                    "Error: --event-id, --name, and --email are required for --register",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = register_attendee(
                config=config,
                settings=settings,
                event_id=args.event_id,
                name=args.name,
                email=args.email,
                company=args.company,
                phone=args.phone,
                ticket_type=args.ticket_type,
                dietary_restrictions=args.dietary_restrictions,
                special_requests=args.special_requests,
            )

            if result["success"]:
                print(f"\nRegistration successful:")
                print(f"Registration ID: {result['registration_id']}")
                print(f"Status: {result['status']}")
                if result.get("is_waitlist"):
                    print(f"Waitlist Position: {result.get('waitlist_position')}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.generate_list:
            if not args.event_id:
                print("Error: --event-id is required for --generate-list", file=sys.stderr)
                sys.exit(1)

            result = generate_attendee_list(
                config=config,
                settings=settings,
                event_id=args.event_id,
                include_waitlist=args.include_waitlist,
                format=args.format,
            )

            print(f"\nAttendee list generated:")
            print(f"Format: {result['format'].upper()}")
            print(f"Path: {result['report_path']}")

        elif args.generate_badges:
            if not args.event_id:
                print("Error: --event-id is required for --generate-badges", file=sys.stderr)
                sys.exit(1)

            result = generate_badges(
                config=config,
                settings=settings,
                event_id=args.event_id,
                registration_id=args.registration_id,
            )

            print(f"\nBadges generated:")
            print(f"Count: {result['badge_count']}")
            if result["badge_paths"]:
                print(f"First badge: {result['badge_paths'][0]}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
