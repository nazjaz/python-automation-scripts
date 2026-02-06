"""Content Calendar Generator automation system.

Automatically generates personalized content calendars by analyzing audience
engagement, optimal posting times, and content performance, with automated
scheduling across platforms.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.calendar_generator import CalendarGenerator
from src.config import get_settings, load_config
from src.platform_scheduler import PlatformScheduler


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/content_calendar.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=log_config.get("max_bytes", 10485760),
        backupCount=log_config.get("backup_count", 5),
    )

    formatter = logging.Formatter(log_config.get("format"))
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    log_level = getattr(logging, log_config.get("level", "INFO").upper())
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def load_historical_data(data_path: Optional[Path]) -> Dict[str, List[Dict]]:
    """Load historical post data from JSON file.

    Args:
        data_path: Path to JSON file containing historical data.

    Returns:
        Dictionary mapping platform names to lists of post data.
    """
    if not data_path or not data_path.exists():
        return {}

    try:
        with open(data_path, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"default": data}
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error loading historical data: {e}")
        return {}


def save_calendar(calendar: Dict[str, List[Dict]], output_path: Path) -> None:
    """Save generated calendar to JSON file.

    Args:
        calendar: Calendar dictionary mapping platforms to posts.
        output_path: Path to save calendar file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(calendar, f, indent=2, default=str)

    logging.info(f"Calendar saved to {output_path}")


def generate_calendar(
    settings,
    platforms: List[str],
    historical_data_path: Optional[Path] = None,
    start_date: Optional[datetime] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, List[Dict]]:
    """Generate content calendar for specified platforms.

    Args:
        settings: Application settings.
        platforms: List of platform names to generate calendars for.
        historical_data_path: Path to historical data file.
        start_date: Start date for calendar generation.
        output_path: Path to save generated calendar.

    Returns:
        Dictionary mapping platform names to their calendars.
    """
    generator = CalendarGenerator(settings)

    historical_data = None
    if historical_data_path:
        historical_data = load_historical_data(historical_data_path)

    calendar = generator.generate_multi_platform_calendar(
        platforms, historical_data, start_date
    )

    if output_path:
        save_calendar(calendar, output_path)

    return calendar


def schedule_calendar(
    settings, calendar: Dict[str, List[Dict]]
) -> Dict[str, Dict]:
    """Schedule posts from calendar across platforms.

    Args:
        settings: Application settings.
        calendar: Calendar dictionary mapping platforms to posts.

    Returns:
        Dictionary with scheduling results per platform.
    """
    scheduler = PlatformScheduler(settings)
    return scheduler.schedule_calendar(calendar)


def main() -> int:
    """Main entry point for content calendar generator.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = argparse.ArgumentParser(
        description="Generate personalized content calendars for social media"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["facebook", "twitter"],
        help="Platforms to generate calendars for",
    )
    parser.add_argument(
        "--historical-data",
        type=Path,
        help="Path to historical post data JSON file",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for calendar (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("calendars/calendar.json"),
        help="Output path for generated calendar",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Automatically schedule posts after generation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate calendar without scheduling",
    )

    args = parser.parse_args()

    try:
        settings = (
            load_config(args.config) if args.config else get_settings()
        )
        setup_logging(settings.logging.dict())

        start_date = None
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")

        logging.info("Starting content calendar generation")
        logging.info(f"Platforms: {', '.join(args.platforms)}")

        calendar = generate_calendar(
            settings,
            args.platforms,
            args.historical_data,
            start_date,
            args.output,
        )

        total_posts = sum(len(posts) for posts in calendar.values())
        logging.info(f"Generated calendar with {total_posts} total posts")

        if args.schedule and not args.dry_run:
            logging.info("Scheduling posts across platforms")
            results = schedule_calendar(settings, calendar)

            total_scheduled = sum(
                r.get("scheduled", 0) for r in results.values()
            )
            total_failed = sum(r.get("failed", 0) for r in results.values())

            logging.info(
                f"Scheduling complete: {total_scheduled} scheduled, "
                f"{total_failed} failed"
            )

        return 0

    except KeyboardInterrupt:
        logging.warning("Interrupted by user")
        return 130
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
