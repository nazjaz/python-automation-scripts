"""Personalized learning recommendation automation system.

Generates personalized learning recommendations by analyzing user behavior,
course completion rates, and learning objectives with adaptive difficulty.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.behavior_analyzer import BehaviorAnalyzer
from src.completion_analyzer import CompletionAnalyzer
from src.difficulty_adapter import DifficultyAdapter
from src.objective_tracker import ObjectiveTracker
from src.recommendation_generator import RecommendationGenerator
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/learning_recommender.log"))
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


def analyze_behavior(
    config: dict,
    settings: object,
    user_id: str,
) -> dict:
    """Analyze user behavior.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.

    Returns:
        Dictionary with behavior analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    user = db_manager.get_user(user_id)
    if not user:
        logger.warning(f"User not found: {user_id}")
        return {"success": False, "error": "User not found"}

    analyzer = BehaviorAnalyzer(db_manager, config.get("behavior_analysis", {}))
    behavior_analysis = analyzer.analyze_user_behavior(user.id)
    learning_style = analyzer.get_learning_style(user.id)

    logger.info(f"Behavior analysis completed for user {user_id}")

    return {
        "success": True,
        "behavior_analysis": behavior_analysis,
        "learning_style": learning_style,
    }


def analyze_completion(
    config: dict,
    settings: object,
    course_id: str,
    days: Optional[int] = None,
) -> dict:
    """Analyze course completion rates.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        course_id: Course identifier.
        days: Number of days to analyze.

    Returns:
        Dictionary with completion analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = CompletionAnalyzer(db_manager, config.get("completion_analysis", {}))

    course = db_manager.get_course(course_id)
    if not course:
        logger.warning(f"Course not found: {course_id}")
        return {"success": False, "error": "Course not found"}

    logger.info(f"Analyzing completion rate for course {course_id}")

    completion_rate = analyzer.analyze_completion_rate(course.id, days=days)
    trends = analyzer.get_course_completion_trends(course.id, days=days or 30)

    logger.info(f"Completion rate: {completion_rate.get('completion_rate', 0.0):.2f}%")

    return {
        "success": True,
        "completion_rate": completion_rate,
        "trends": trends,
    }


def adapt_difficulty(
    config: dict,
    settings: object,
    user_id: str,
    course_id: str,
) -> dict:
    """Adapt difficulty level.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.
        course_id: Course identifier.

    Returns:
        Dictionary with difficulty adaptation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    adapter = DifficultyAdapter(db_manager, config.get("difficulty_adaptation", {}))

    user = db_manager.get_user(user_id)
    course = db_manager.get_course(course_id)

    if not user or not course:
        logger.warning(f"User or course not found: {user_id}, {course_id}")
        return {"success": False, "error": "User or course not found"}

    logger.info(f"Adapting difficulty for user {user_id}, course {course_id}")

    difficulty_rec = adapter.adapt_difficulty(user.id, course.id)

    logger.info(f"Recommended difficulty: {difficulty_rec.get('recommended_difficulty', 'unknown')}")

    return {
        "success": True,
        "difficulty_recommendation": difficulty_rec,
    }


def track_objectives(
    config: dict,
    settings: object,
    user_id: str,
) -> dict:
    """Track learning objectives.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.

    Returns:
        Dictionary with objective tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ObjectiveTracker(db_manager, config.get("objective_tracking", {}))

    user = db_manager.get_user(user_id)
    if not user:
        logger.warning(f"User not found: {user_id}")
        return {"success": False, "error": "User not found"}

    logger.info(f"Tracking objectives for user {user_id}")

    objectives_summary = tracker.get_user_objectives_summary(user.id)

    logger.info(f"Found {objectives_summary.get('total_objectives', 0)} objectives")

    return {
        "success": True,
        "objectives_summary": objectives_summary,
    }


def generate_recommendations(
    config: dict,
    settings: object,
    user_id: str,
    limit: int = 10,
) -> dict:
    """Generate personalized recommendations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        user_id: User identifier.
        limit: Maximum number of recommendations.

    Returns:
        Dictionary with recommendation generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = RecommendationGenerator(
        db_manager, config.get("recommendations", {})
    )

    user = db_manager.get_user(user_id)
    if not user:
        logger.warning(f"User not found: {user_id}")
        return {"success": False, "error": "User not found"}

    logger.info(f"Generating recommendations for user {user_id}")

    recommendations = generator.generate_recommendations(user.id, limit=limit)

    logger.info(f"Generated {len(recommendations)} recommendations")

    return {
        "success": True,
        "recommendations_generated": len(recommendations),
        "recommendations": recommendations,
    }


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

    logger.info("Generating learning recommendation reports", extra={"user_id": user_id})

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
    """Main entry point for learning recommendation automation."""
    parser = argparse.ArgumentParser(
        description="Personalized learning recommendation automation system"
    )
    parser.add_argument(
        "--analyze-behavior",
        metavar="USER_ID",
        help="Analyze user behavior",
    )
    parser.add_argument(
        "--analyze-completion",
        metavar="COURSE_ID",
        help="Analyze course completion rates",
    )
    parser.add_argument(
        "--adapt-difficulty",
        nargs=2,
        metavar=("USER_ID", "COURSE_ID"),
        help="Adapt difficulty level",
    )
    parser.add_argument(
        "--track-objectives",
        metavar="USER_ID",
        help="Track learning objectives",
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
        "--days",
        type=int,
        help="Number of days to analyze",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.analyze_behavior,
        args.analyze_completion,
        args.adapt_difficulty,
        args.track_objectives,
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
        if args.analyze_behavior:
            result = analyze_behavior(
                config=config,
                settings=settings,
                user_id=args.analyze_behavior,
            )
            if result.get("success"):
                print(f"\nBehavior analysis completed:")
                print(f"Learning style: {result['learning_style'].get('learning_style', 'unknown')}")
                print(f"Total behaviors: {result['behavior_analysis'].get('total_behaviors', 0)}")

        if args.analyze_completion:
            result = analyze_completion(
                config=config,
                settings=settings,
                course_id=args.analyze_completion,
                days=args.days,
            )
            if result.get("success"):
                print(f"\nCompletion analysis completed:")
                print(f"Completion rate: {result['completion_rate'].get('completion_rate', 0.0):.2f}%")
                print(f"Trend: {result['trends'].get('trend', 'unknown')}")

        if args.adapt_difficulty:
            user_id, course_id = args.adapt_difficulty
            result = adapt_difficulty(
                config=config,
                settings=settings,
                user_id=user_id,
                course_id=course_id,
            )
            if result.get("success"):
                print(f"\nDifficulty adaptation completed:")
                rec = result["difficulty_recommendation"]
                print(f"Recommended difficulty: {rec.get('recommended_difficulty', 'unknown')}")
                print(f"Confidence: {rec.get('confidence', 0.0):.2f}")

        if args.track_objectives:
            result = track_objectives(
                config=config,
                settings=settings,
                user_id=args.track_objectives,
            )
            if result.get("success"):
                print(f"\nObjective tracking completed:")
                summary = result["objectives_summary"]
                print(f"Total objectives: {summary.get('total_objectives', 0)}")
                print(f"Average progress: {summary.get('average_progress', 0.0):.2%}")

        if args.generate_recommendations:
            result = generate_recommendations(
                config=config,
                settings=settings,
                user_id=args.generate_recommendations,
                limit=args.limit,
            )
            if result.get("success"):
                print(f"\nRecommendations generated: {result['recommendations_generated']}")
                for rec in result["recommendations"][:5]:
                    print(f"  - {rec['course_name']} (confidence: {rec['confidence_score']:.2f})")

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
