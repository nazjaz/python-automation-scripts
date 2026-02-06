"""Content performance monitoring automation system.

Monitors content performance across platforms, analyzes engagement metrics,
identifies top-performing content, and generates content strategy recommendations.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.metrics_analyzer import MetricsAnalyzer
from src.platform_connector import PlatformManager
from src.report_generator import ReportGenerator
from src.strategy_recommender import StrategyRecommender
from src.top_content_identifier import TopContentIdentifier


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/content_performance.log"))
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


def collect_content_data(
    config: dict,
    settings: object,
    days: int = 30,
    limit: int = 100,
) -> dict:
    """Collect content data from all enabled platforms.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        days: Number of days to look back.
        limit: Maximum content items per platform.

    Returns:
        Dictionary with collection results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    platform_configs = config.get("platforms", [])
    platform_manager = PlatformManager(db_manager, platform_configs)

    logger.info("Starting content data collection", extra={"days": days, "limit": limit})

    platform_data = platform_manager.collect_content_data(limit=limit, days=days)
    platform_manager.store_content_data(platform_data)

    total_items = sum(len(items) for items in platform_data.values())

    logger.info(
        f"Content data collection completed: {total_items} items collected",
        extra={"total_items": total_items},
    )

    return {
        "success": True,
        "total_items": total_items,
        "platforms": {k: len(v) for k, v in platform_data.items()},
    }


def analyze_content_performance(
    config: dict,
    settings: object,
    platform: Optional[str] = None,
    days: Optional[int] = None,
) -> dict:
    """Analyze content performance and calculate scores.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        platform: Optional platform filter.
        days: Optional number of days to analyze.

    Returns:
        Dictionary with analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    platform_configs = config.get("platforms", [])

    if days is None:
        days = config.get("analysis", {}).get("analysis_period_days", 30)

    analyzer = MetricsAnalyzer(db_manager, platform_configs)

    logger.info("Starting content performance analysis", extra={"platform": platform, "days": days})

    analyzed_count = analyzer.analyze_all_content(platform=platform, days=days)

    logger.info(
        f"Content analysis completed: {analyzed_count} items analyzed",
        extra={"analyzed_count": analyzed_count, "platform": platform},
    )

    return {
        "success": True,
        "analyzed_count": analyzed_count,
        "platform": platform,
    }


def generate_strategy_report(
    config: dict,
    settings: object,
    platform: Optional[str] = None,
) -> dict:
    """Generate content strategy report with recommendations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        platform: Optional platform filter.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    platform_configs = config.get("platforms", [])

    top_content_identifier = TopContentIdentifier(
        db_manager,
        top_count=config.get("analysis", {}).get("top_content_count", 10),
    )

    strategy_recommender = StrategyRecommender(
        db_manager, top_content_identifier, config
    )

    report_generator = ReportGenerator(
        db_manager, top_content_identifier, strategy_recommender, config
    )

    logger.info("Generating content strategy report", extra={"platform": platform})

    reports = report_generator.generate_reports(platform=platform)

    logger.info(
        f"Strategy report generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports), "platform": platform},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "platform": platform,
    }


def main() -> None:
    """Main entry point for content performance monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Content performance monitoring automation system"
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Collect content data from platforms",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze content performance and calculate scores",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate content strategy report",
    )
    parser.add_argument(
        "--platform",
        help="Filter by specific platform (facebook, twitter, instagram, linkedin, youtube)",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to look back (default: 30)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum content items per platform (default: 100)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([args.collect, args.analyze, args.report]):
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
        if args.collect:
            days = args.days or config.get("analysis", {}).get("analysis_period_days", 30)
            result = collect_content_data(
                config=config,
                settings=settings,
                days=days,
                limit=args.limit,
            )
            print(f"\nContent collection completed:")
            print(f"Total items collected: {result['total_items']}")
            for platform, count in result["platforms"].items():
                print(f"  {platform}: {count} items")

        if args.analyze:
            days = args.days or config.get("analysis", {}).get("analysis_period_days", 30)
            result = analyze_content_performance(
                config=config,
                settings=settings,
                platform=args.platform,
                days=days,
            )
            print(f"\nContent analysis completed:")
            print(f"Items analyzed: {result['analyzed_count']}")
            if args.platform:
                print(f"Platform: {args.platform}")

        if args.report:
            result = generate_strategy_report(
                config=config,
                settings=settings,
                platform=args.platform,
            )
            print(f"\nStrategy report generated:")
            for report_type, path in result["reports"].items():
                print(f"  {report_type.upper()}: {path}")
            if args.platform:
                print(f"Platform: {args.platform}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
