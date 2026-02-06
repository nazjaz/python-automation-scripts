"""Personalized content recommendation automation system.

Generates personalized content recommendations by analyzing user preferences,
viewing history, and engagement patterns across multiple content types.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.preference_analyzer import PreferenceAnalyzer
from src.history_analyzer import HistoryAnalyzer
from src.engagement_analyzer import EngagementAnalyzer
from src.recommendation_generator import RecommendationGenerator
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/content_recommender.log"))
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


def analyze_preferences(
    config: dict,
    settings: object,
    user_id: str,
) -> dict:
    """Analyze user preferences.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.

    Returns:
        Dictionary with preference analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = PreferenceAnalyzer(db_manager, config.get("preference_analysis", {}))

    logger.info(f"Analyzing preferences for user: {user_id}")

    result = analyzer.analyze_preferences(user_id)

    logger.info(f"Found {result.get('total_preferences', 0)} preferences")

    return result


def extract_preferences_from_history(
    config: dict,
    settings: object,
    user_id: str,
) -> dict:
    """Extract preferences from viewing history.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.

    Returns:
        Dictionary with extraction results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = PreferenceAnalyzer(db_manager, config.get("preference_analysis", {}))

    logger.info(f"Extracting preferences from history for user: {user_id}")

    result = analyzer.extract_preferences_from_history(user_id)

    logger.info(f"Extracted {result.get('extracted_preferences', 0)} preferences")

    return result


def analyze_history(
    config: dict,
    settings: object,
    user_id: str,
    days: int = 30,
) -> dict:
    """Analyze viewing history.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.
        days: Number of days to analyze.

    Returns:
        Dictionary with history analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = HistoryAnalyzer(db_manager, config.get("history_analysis", {}))

    logger.info(f"Analyzing viewing history for user: {user_id}")

    result = analyzer.analyze_history(user_id, days=days)

    logger.info(f"Found {result.get('recent_views', 0)} recent views")

    return result


def analyze_engagement(
    config: dict,
    settings: object,
    user_id: str,
    days: int = 30,
) -> dict:
    """Analyze engagement patterns.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.
        days: Number of days to analyze.

    Returns:
        Dictionary with engagement analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = EngagementAnalyzer(db_manager, config.get("engagement_analysis", {}))

    logger.info(f"Analyzing engagement patterns for user: {user_id}")

    result = analyzer.analyze_engagement(user_id, days=days)

    logger.info(f"Total engagement: {result.get('total_engagement', 0):.2f}")

    return result


def generate_recommendations(
    config: dict,
    settings: object,
    user_id: str,
    limit: int = 10,
    content_type: Optional[str] = None,
) -> dict:
    """Generate personalized recommendations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.
        limit: Maximum number of recommendations.
        content_type: Optional content type filter.

    Returns:
        Dictionary with recommendation generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = RecommendationGenerator(
        db_manager, config.get("recommendation", {})
    )

    logger.info(f"Generating recommendations for user: {user_id}")

    result = generator.generate_recommendations(
        user_id, limit=limit, content_type=content_type
    )

    logger.info(
        f"Generated {result.get('recommendations_created', 0)} recommendations"
    )

    return result


def generate_reports(
    config: dict,
    settings: object,
    user_id: Optional[str] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: Optional user ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating content recommendation reports", extra={"user_id": user_id})

    reports = report_generator.generate_reports(user_id=user_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "user_id": user_id,
    }


def main() -> None:
    """Main entry point for content recommendation automation."""
    parser = argparse.ArgumentParser(
        description="Personalized content recommendation automation system"
    )
    parser.add_argument(
        "--analyze-preferences",
        metavar="USER_ID",
        help="Analyze user preferences",
    )
    parser.add_argument(
        "--extract-preferences",
        metavar="USER_ID",
        help="Extract preferences from viewing history",
    )
    parser.add_argument(
        "--analyze-history",
        metavar="USER_ID",
        help="Analyze viewing history",
    )
    parser.add_argument(
        "--analyze-engagement",
        metavar="USER_ID",
        help="Analyze engagement patterns",
    )
    parser.add_argument(
        "--generate-recommendations",
        metavar="USER_ID",
        help="Generate personalized recommendations",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--user-id",
        help="Filter by user ID",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of recommendations (default: 10)",
    )
    parser.add_argument(
        "--content-type",
        help="Filter by content type",
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
        args.analyze_preferences,
        args.extract_preferences,
        args.analyze_history,
        args.analyze_engagement,
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
        if args.analyze_preferences:
            result = analyze_preferences(
                config=config,
                settings=settings,
                user_id=args.analyze_preferences,
            )
            print(f"\nPreference Analysis:")
            print(f"Total preferences: {result.get('total_preferences', 0)}")
            print(f"Preference types: {', '.join(result.get('preference_types', []))}")

        if args.extract_preferences:
            result = extract_preferences_from_history(
                config=config,
                settings=settings,
                user_id=args.extract_preferences,
            )
            print(f"\nPreference Extraction:")
            print(f"Extracted preferences: {result.get('extracted_preferences', 0)}")

        if args.analyze_history:
            result = analyze_history(
                config=config,
                settings=settings,
                user_id=args.analyze_history,
                days=args.days,
            )
            print(f"\nHistory Analysis:")
            print(f"Recent views: {result.get('recent_views', 0)}")
            print(f"Average rating: {result.get('average_rating', 0):.2f}")
            print(f"Average completion: {result.get('average_completion', 0):.1f}%")

        if args.analyze_engagement:
            result = analyze_engagement(
                config=config,
                settings=settings,
                user_id=args.analyze_engagement,
                days=args.days,
            )
            print(f"\nEngagement Analysis:")
            print(f"Total engagement: {result.get('total_engagement', 0):.2f}")

        if args.generate_recommendations:
            result = generate_recommendations(
                config=config,
                settings=settings,
                user_id=args.generate_recommendations,
                limit=args.limit,
                content_type=args.content_type,
            )
            if result.get("success"):
                print(f"\nRecommendations Generated:")
                print(f"Recommendations created: {result.get('recommendations_created', 0)}")
                for rec in result.get("recommendations", [])[:5]:
                    print(f"  - {rec['title']} (score: {rec['score']:.2f})")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                user_id=args.user_id,
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
