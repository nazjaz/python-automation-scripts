"""Fitness challenge automation system.

Generates personalized fitness challenges, sets goals, tracks progress,
creates leaderboards, and sends motivational messages to participants.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.challenge_generator import ChallengeGenerator
from src.goal_setter import GoalSetter
from src.progress_tracker import ProgressTracker
from src.leaderboard_generator import LeaderboardGenerator
from src.message_sender import MessageSender
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/fitness_challenge.log"))
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


def add_participant(
    config: dict,
    settings: object,
    name: str,
    email: str,
    phone: Optional[str] = None,
    fitness_level: Optional[str] = None,
) -> dict:
    """Add a new participant.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        name: Participant name.
        email: Participant email.
        phone: Participant phone number.
        fitness_level: Fitness level.

    Returns:
        Dictionary with participant information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    logger.info(f"Adding participant: {name} ({email})")

    participant = db_manager.add_participant(
        name=name,
        email=email,
        phone=phone,
        fitness_level=fitness_level,
    )

    logger.info(f"Participant added: ID {participant.id}")

    return {
        "success": True,
        "participant_id": participant.id,
        "name": participant.name,
        "email": participant.email,
    }


def generate_challenges(
    config: dict,
    settings: object,
    participant_id: int,
    count: int = 3,
) -> dict:
    """Generate personalized challenges for participant.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        participant_id: Participant ID.
        count: Number of challenges to generate.

    Returns:
        Dictionary with challenge generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    challenge_generator = ChallengeGenerator(db_manager, config.get("challenges", {}))

    logger.info(f"Generating challenges for participant {participant_id}")

    challenges = challenge_generator.generate_personalized_challenges(
        participant_id=participant_id, count=count
    )

    logger.info(f"Generated {len(challenges)} challenges")

    return {
        "success": True,
        "challenges_generated": len(challenges),
        "challenges": challenges,
    }


def set_goals(
    config: dict,
    settings: object,
    participant_id: int,
) -> dict:
    """Set personalized goals for participant.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        participant_id: Participant ID.

    Returns:
        Dictionary with goal setting results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    goal_setter = GoalSetter(db_manager, config.get("goals", {}))

    logger.info(f"Setting goals for participant {participant_id}")

    goals = goal_setter.set_personalized_goals(participant_id=participant_id)

    logger.info(f"Set {len(goals)} goals")

    return {
        "success": True,
        "goals_set": len(goals),
        "goals": goals,
    }


def record_progress(
    config: dict,
    settings: object,
    participant_id: int,
    value: float,
    unit: str,
    challenge_id: Optional[int] = None,
    goal_id: Optional[int] = None,
) -> dict:
    """Record progress entry.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        participant_id: Participant ID.
        value: Progress value.
        unit: Unit of measurement.
        challenge_id: Optional challenge ID.
        goal_id: Optional goal ID.

    Returns:
        Dictionary with progress recording results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    progress_tracker = ProgressTracker(db_manager, config.get("progress", {}))

    logger.info(f"Recording progress for participant {participant_id}")

    progress_entry = progress_tracker.record_progress(
        participant_id=participant_id,
        value=value,
        unit=unit,
        challenge_id=challenge_id,
        goal_id=goal_id,
    )

    logger.info(f"Progress recorded: {value} {unit}")

    return {
        "success": True,
        "progress_entry_id": progress_entry["id"],
        "value": progress_entry["value"],
        "unit": progress_entry["unit"],
    }


def update_leaderboard(
    config: dict,
    settings: object,
    challenge_id: Optional[int] = None,
) -> dict:
    """Update leaderboard.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        challenge_id: Optional challenge ID.

    Returns:
        Dictionary with leaderboard update results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    leaderboard_generator = LeaderboardGenerator(
        db_manager, config.get("leaderboard", {})
    )

    logger.info("Updating leaderboard", extra={"challenge_id": challenge_id})

    entries_updated = leaderboard_generator.update_leaderboard(challenge_id=challenge_id)

    logger.info(f"Leaderboard updated: {entries_updated} entries")

    return {
        "success": True,
        "entries_updated": entries_updated,
        "challenge_id": challenge_id,
    }


def send_messages(
    config: dict,
    settings: object,
    participant_id: Optional[int] = None,
    message_type: str = "motivational",
) -> dict:
    """Send motivational messages.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        participant_id: Optional participant ID. If None, sends to all.
        message_type: Message type.

    Returns:
        Dictionary with message sending results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    message_sender = MessageSender(db_manager, config.get("messages", {}))

    if participant_id:
        logger.info(f"Sending {message_type} message to participant {participant_id}")
        message = message_sender.send_motivational_message(participant_id, message_type)
        messages_sent = 1 if message else 0
    else:
        logger.info(f"Sending {message_type} messages to all participants")
        messages = message_sender.send_bulk_messages(message_type=message_type)
        messages_sent = len(messages)

    logger.info(f"Messages sent: {messages_sent}")

    return {
        "success": True,
        "messages_sent": messages_sent,
        "message_type": message_type,
    }


def generate_reports(
    config: dict,
    settings: object,
    participant_id: Optional[int] = None,
    challenge_id: Optional[int] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        participant_id: Optional participant ID to filter by.
        challenge_id: Optional challenge ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating fitness challenge reports", extra={"participant_id": participant_id, "challenge_id": challenge_id})

    reports = report_generator.generate_reports(
        participant_id=participant_id, challenge_id=challenge_id
    )

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "participant_id": participant_id,
        "challenge_id": challenge_id,
    }


def main() -> None:
    """Main entry point for fitness challenge automation."""
    parser = argparse.ArgumentParser(description="Fitness challenge automation system")
    parser.add_argument(
        "--add-participant",
        nargs=2,
        metavar=("NAME", "EMAIL"),
        help="Add a new participant",
    )
    parser.add_argument(
        "--generate-challenges",
        type=int,
        metavar="PARTICIPANT_ID",
        help="Generate personalized challenges for participant",
    )
    parser.add_argument(
        "--set-goals",
        type=int,
        metavar="PARTICIPANT_ID",
        help="Set personalized goals for participant",
    )
    parser.add_argument(
        "--record-progress",
        nargs=3,
        metavar=("PARTICIPANT_ID", "VALUE", "UNIT"),
        help="Record progress entry",
    )
    parser.add_argument(
        "--update-leaderboard",
        action="store_true",
        help="Update leaderboard",
    )
    parser.add_argument(
        "--send-messages",
        action="store_true",
        help="Send motivational messages",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--participant-id",
        type=int,
        help="Filter by participant ID",
    )
    parser.add_argument(
        "--challenge-id",
        type=int,
        help="Filter by challenge ID",
    )
    parser.add_argument(
        "--message-type",
        default="motivational",
        help="Message type (default: motivational)",
    )
    parser.add_argument(
        "--challenge-count",
        type=int,
        default=3,
        help="Number of challenges to generate (default: 3)",
    )
    parser.add_argument(
        "--phone",
        help="Participant phone number",
    )
    parser.add_argument(
        "--fitness-level",
        choices=["beginner", "intermediate", "advanced"],
        help="Participant fitness level",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.add_participant,
        args.generate_challenges,
        args.set_goals,
        args.record_progress,
        args.update_leaderboard,
        args.send_messages,
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
        if args.add_participant:
            name, email = args.add_participant
            result = add_participant(
                config=config,
                settings=settings,
                name=name,
                email=email,
                phone=args.phone,
                fitness_level=args.fitness_level,
            )
            print(f"\nParticipant added:")
            print(f"ID: {result['participant_id']}")
            print(f"Name: {result['name']}")
            print(f"Email: {result['email']}")

        if args.generate_challenges:
            result = generate_challenges(
                config=config,
                settings=settings,
                participant_id=args.generate_challenges,
                count=args.challenge_count,
            )
            print(f"\nChallenges generated: {result['challenges_generated']}")

        if args.set_goals:
            result = set_goals(
                config=config,
                settings=settings,
                participant_id=args.set_goals,
            )
            print(f"\nGoals set: {result['goals_set']}")

        if args.record_progress:
            participant_id, value, unit = args.record_progress
            result = record_progress(
                config=config,
                settings=settings,
                participant_id=int(participant_id),
                value=float(value),
                unit=unit,
                challenge_id=args.challenge_id,
            )
            print(f"\nProgress recorded:")
            print(f"Value: {result['value']} {result['unit']}")

        if args.update_leaderboard:
            result = update_leaderboard(
                config=config,
                settings=settings,
                challenge_id=args.challenge_id,
            )
            print(f"\nLeaderboard updated:")
            print(f"Entries updated: {result['entries_updated']}")

        if args.send_messages:
            result = send_messages(
                config=config,
                settings=settings,
                participant_id=args.participant_id,
                message_type=args.message_type,
            )
            print(f"\nMessages sent: {result['messages_sent']}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                participant_id=args.participant_id,
                challenge_id=args.challenge_id,
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
